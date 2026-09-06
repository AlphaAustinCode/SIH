from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import TrainSchedule
from app.schemas.train import TrainScheduleResponse

router = APIRouter(prefix="/trains", tags=["Trains"])

@router.get("/", response_model=List[TrainScheduleResponse])
def get_all_trains(section_code: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(TrainSchedule)
    if section_code:
        query = query.filter(TrainSchedule.section_code == section_code)
    return query.offset(skip).limit(limit).all()