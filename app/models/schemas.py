from typing import List, Optional
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class ActionType(str, Enum):
    CALENDAR_EVENT = "CALENDAR_EVENT"
    SHOPPING_ITEM = "SHOPPING_ITEM"
    TODO = "TODO"
    NOTE = "NOTE"
    ALARM = "ALARM"
    REMINDER = "REMINDER"

class ProcessedAction(BaseModel):
    type: ActionType
    content: str
    category: Optional[str] = None
    datetime_iso: Optional[datetime] = None
    delay_seconds: Optional[int] = None
    priority: Optional[str] = None
    confidence: float

class BrainDumpResponse(BaseModel):
    summary: str
    actions: List[ProcessedAction]

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str

# User Profile Schemas
class UserBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    morning_briefing_time: Optional[str] = "09:00"

class UserUpdate(UserBase):
    is_google_calendar_connected: Optional[bool] = None
    is_notion_connected: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_google_calendar_connected: bool
    is_notion_connected: bool
    
    class Config:
        orm_mode = True

