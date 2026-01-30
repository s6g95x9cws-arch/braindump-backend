from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from app.api import audio_processor, actions
from sqlalchemy.orm import Session
from ..services.ai_service import AIService
from ..models import schemas, sql_models
from ..core.database import get_db
from datetime import datetime
import shutil
import shutil
import os
import time

router = APIRouter()

router.include_router(audio_processor.router, prefix="/audio", tags=["audio"])
router.include_router(actions.router, prefix="/actions", tags=["actions"])

@router.post("/ask", response_model=schemas.AnswerResponse)
async def ask_question(
    request: schemas.QuestionRequest,
    db: Session = Depends(get_db)
):
    # 1. Fetch recent actions (Context)
    # Limit to last 50 items to keep context size manageable
    actions = db.query(sql_models.Action).order_by(sql_models.Action.created_at.desc()).limit(50).all()
    
    # 2. Get Answer
    # ai_service is instantiated globally in endpoints, but let's use a fresh one or the global one.
    # The global 'ai_service' variable is not available here, we need to instantiate it.
    # Waiting, checking imports... 'ai_service' variable created at end of ai_service.py?
    # No, it is instantiated at the end of ai_service.py as 'ai_service = AIService()'.
    # So we can import it.
    
    from ..services.ai_service import ai_service
    
    answer_text = await ai_service.answer_question(actions, request.question)
    
    return {"answer": answer_text}

# --- USER PROFILE ENDPOINTS ---
@router.get("/user", response_model=schemas.UserResponse)
async def get_user_profile(db: Session = Depends(get_db)):
    # Simulating single user for MVP
    user = db.query(sql_models.User).first()
    if not user:
        # Auto-create default user
        user = sql_models.User(full_name="BrainDump User", email="user@braindump.app")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.patch("/user", response_model=schemas.UserResponse)
async def update_user_profile(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db)
):
    user = db.query(sql_models.User).first()
    if not user:
        user = sql_models.User()
        db.add(user)
    
    # Update fields
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.morning_briefing_time is not None:
        user.morning_briefing_time = user_update.morning_briefing_time
    
    # Handle Booleans manually for SQLite compliance if needed, but SQLAlchemy usually handles bool->int mapping.
    # Let's trust SQLAlchemy TypeDecorator or standard bool behavior, but for SQLite safer to cast if we declared Integer.
    # I declared Integer in sql_models, so I should map bool to int here explicitly to be safe.
    
    if user_update.is_google_calendar_connected is not None:
        user.is_google_calendar_connected = 1 if user_update.is_google_calendar_connected else 0
    if user_update.is_notion_connected is not None:
        user.is_notion_connected = 1 if user_update.is_notion_connected else 0

    db.commit()
    db.refresh(user)
    db.commit()
    db.refresh(user)
    return user

# --- VISION ENDPOINTS ---
@router.post("/process-image", response_model=schemas.BrainDumpResponse)
async def process_image_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Save temp file
    temp_filename = f"temp_{int(time.time())}_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        from ..services.ai_service import ai_service
        
        # 2. Process with Gemini Vision
        brain_dump = await ai_service.process_image(temp_filename)
        
        # 3. Save Actions to DB
        created_actions_db = []
        for action in brain_dump.actions:
            db_action = sql_models.Action(
                type=action.type,
                content=action.content,
                category=action.category,
                datetime_iso=action.datetime_iso,
                priority=action.priority,
                confidence=action.confidence
            )
            db.add(db_action)
            created_actions_db.append(db_action)
        
        db.commit()
        
        # 4. Refresh IDs
        for a in created_actions_db:
            db.refresh(a)
            
        return brain_dump
        
    except Exception as e:
        print(f"Image processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
