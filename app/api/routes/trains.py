from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database.models import TrainSchedule
from app.database.session import get_db
from app.schemas.train import TrainScheduleResponse

router = APIRouter(prefix="/api/trains", tags=["trains"])


@router.get("", response_model=list[TrainScheduleResponse])
def list_trains(
    track_section_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = (
        db.query(TrainSchedule)
        .options(joinedload(TrainSchedule.track_section))
        .order_by(TrainSchedule.scheduled_entry)
    )
    if track_section_id is not None:
        query = query.filter(TrainSchedule.track_section_id == track_section_id)
    return query.offset(skip).limit(limit).all()
