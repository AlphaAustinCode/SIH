from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import TrackSection
from app.schemas.track import TrackSectionResponse

router = APIRouter(prefix="/tracks", tags=["Tracks"])

@router.get("/", response_model=List[TrackSectionResponse])
def get_all_tracks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(TrackSection).offset(skip).limit(limit).all()

@router.get("/{section_code}", response_model=TrackSectionResponse)
def get_track_by_code(section_code: str, db: Session = Depends(get_db)):
    track = db.query(TrackSection).filter(TrackSection.section_code == section_code).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track section not found")
    return track