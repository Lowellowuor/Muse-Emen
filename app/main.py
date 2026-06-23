from fastapi import FastAPI
from app.database import engine, Base, SessionLocal
from app.models import User
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Muse MVP - Intelligence Layer", version="1.0")
app.include_router(router)

@app.on_event("startup")
def seed_database():
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.id == "test-user-001").first()
        if not existing_user:
            print("🌱 Seeding test user...")
            test_user = User(
                id="test-user-001",
                email="demo@muse.ai",
                name="Demo User"
            )
            db.add(test_user)
            db.commit()
            print("✅ Test user created.")
        else:
            print("✅ Test user already exists.")
    finally:
        db.close()

@app.get("/")
def health_check():
    return {"status": "Muse Intelligence Engine is running!"}