from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import logging

from app.database import get_db
from app.models import Reflection, ReflectionInsight, User
from app.nlp_engine import NLPEngineFactory, InsightResult

router = APIRouter()
logger = logging.getLogger(__name__)

class ReflectionCreate(BaseModel):
    user_id: str
    text: str

class MirrorResponse(BaseModel):
    topThemes: list[dict]
    recentInsights: list[dict]

def process_reflection_background(reflection_id: str, text: str, user_id: str):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found in background task.")
            return

        engine = NLPEngineFactory.get_engine()
        insights = engine.analyze(text)

        
        reflection_id_str = str(reflection_id)

        for theme in insights.themes:
            insight_entry = ReflectionInsight(
                reflection_id=reflection_id_str,
                user_id=user.id,
                theme=theme,
                sentiment_score=insights.sentiment_score,
                keywords=",".join(insights.keywords)
            )
            db.add(insight_entry)
        db.commit()
        logger.info(f"Background NLP completed for reflection {reflection_id_str}")
    except Exception as e:
        logger.error(f"Background task failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

@router.post("/api/reflections")
def create_reflection(
    payload: ReflectionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{payload.user_id}' not found.")

    reflection = Reflection(text=payload.text, user_id=user.id)
    db.add(reflection)
    db.commit()
    db.refresh(reflection)

    
    background_tasks.add_task(
        process_reflection_background,
        reflection.id,          
        payload.text,
        user.id
    )
    return {"status": "queued", "reflection_id": reflection.id}

@router.get("/api/mirror", response_model=MirrorResponse)
def get_mirror(
    user_id: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")

    theme_counts = db.query(ReflectionInsight.theme).filter(
        ReflectionInsight.user_id == user.id
    ).all()
    
    theme_dict = {}
    for (theme,) in theme_counts:
        theme_dict[theme] = theme_dict.get(theme, 0) + 1
    
    top_themes = [{"theme": k, "count": v} for k, v in sorted(theme_dict.items(), key=lambda x: x[1], reverse=True)[:10]]

    recent = db.query(Reflection).filter(Reflection.user_id == user.id).order_by(
        Reflection.created_at.desc()
    ).limit(5).all()
    
    timeline = []
    for ref in recent:
        insights = db.query(ReflectionInsight).filter(ReflectionInsight.reflection_id == ref.id).all()
        timeline.append({
            "date": ref.created_at.isoformat() if ref.created_at else "",
            "themes": [ins.theme for ins in insights],
            "snippet": ref.text[:100]
        })

    return MirrorResponse(topThemes=top_themes, recentInsights=timeline)