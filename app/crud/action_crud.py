from sqlalchemy.orm import Session
from app.models.sql_models import Action
from app.models.schemas import ProcessedAction

def create_action(db: Session, action: ProcessedAction):
    db_action = Action(
        type=action.type.value,
        content=action.content,
        category=action.category,
        datetime_iso=action.datetime_iso,
        priority=action.priority,
        confidence=action.confidence
    )
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action

def get_actions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Action).order_by(Action.created_at.desc()).offset(skip).limit(limit).all()

def delete_action(db: Session, action_id: int):
    db_action = db.query(Action).filter(Action.id == action_id).first()
    if db_action:
        db.delete(db_action)
        db.commit()
        return True
    return False
