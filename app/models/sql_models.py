from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base
from datetime import datetime

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)
    content = Column(String)
    category = Column(String, nullable=True)
    datetime_iso = Column(DateTime, nullable=True)
    priority = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    
    # Preferences / Context
    morning_briefing_time = Column(String, default="09:00")
    
    # Integration Status (The Hands)
    is_google_calendar_connected = Column(Integer, default=0) # SQLite uses 0/1 for boolean
    is_notion_connected = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

