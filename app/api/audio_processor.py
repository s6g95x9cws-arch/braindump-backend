from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud import action_crud
import shutil
import os
import tempfile
from app.services.ai_service import ai_service
from app.models.schemas import BrainDumpResponse

router = APIRouter()

@router.post("/process-text", response_model=BrainDumpResponse)
async def process_text_endpoint(text: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """
    Debug endpoint to process text directly without audio.
    Useful for testing the LLM logic without a microphone.
    """
    try:
        # We need to bypass the audio processing in AIService or add a text method
        # Let's modify AIService to handle text directly
        result = await ai_service.process_text(text)
        
        # Save to DB
        for action in result.actions:
            action_crud.create_action(db, action)
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process", response_model=BrainDumpResponse)
async def process_audio_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save uploaded file temporarily
    # Create a temp file path
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename or "audio.m4a")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process with AI
        result = await ai_service.process_audio(temp_file_path)
        
        # Save to DB
        for action in result.actions:
            action_crud.create_action(db, action)
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
