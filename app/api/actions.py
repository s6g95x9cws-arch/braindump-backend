from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.crud import action_crud
from app.models.schemas import ProcessedAction

router = APIRouter()

@router.get("/", response_model=List[ProcessedAction])
def read_actions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    actions = action_crud.get_actions(db, skip=skip, limit=limit)
    # Convert SQL models to Pydantic models manually or let FastAPI handle it if config allows
    return actions

@router.delete("/{action_id}")
def delete_action(action_id: int, db: Session = Depends(get_db)):
    success = action_crud.delete_action(db, action_id)
    if not success:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"status": "success"}
