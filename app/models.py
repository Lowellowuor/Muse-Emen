from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Reflection(Base):
    __tablename__ = "reflections"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ReflectionInsight(Base):
    __tablename__ = "reflection_insights"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reflection_id = Column(String, ForeignKey("reflections.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    theme = Column(String, nullable=False)
    sentiment_score = Column(Float, default=0.0)
    keywords = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())