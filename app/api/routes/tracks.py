from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.models import TrackSection
from app.database.session import get_db
from app.schemas.api import TrackResponse

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


@router.get("", response_model=list[TrackResponse])
def list_tracks(db: Session = Depends(get_db)):
    return db.query(TrackSection).order_by(TrackSection.start_km).all()
