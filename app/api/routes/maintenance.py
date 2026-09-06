from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.models import MaintenanceRequest, MaintenanceStatus, TrackSection
from app.database.session import get_db
from app.schemas.api import MaintenanceCreate, MaintenanceResponse
from app.services.block_service import maintenance_response

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.get("", response_model=list[MaintenanceResponse])
def list_maintenance(
    status: MaintenanceStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(MaintenanceRequest).order_by(MaintenanceRequest.urgency_priority.desc())
    if status is not None:
        query = query.filter(MaintenanceRequest.status == status)
    return [maintenance_response(item) for item in query.all()]


@router.post("", response_model=MaintenanceResponse, status_code=201)
def create_maintenance(payload: MaintenanceCreate, db: Session = Depends(get_db)):
    if db.get(TrackSection, payload.track_section_id) is None:
        raise HTTPException(status_code=404, detail="Track section not found")
    request = MaintenanceRequest(**payload.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)
    return maintenance_response(request)


@router.get("/{request_id}", response_model=MaintenanceResponse)
def get_maintenance(request_id: int, db: Session = Depends(get_db)):
    request = db.get(MaintenanceRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return maintenance_response(request)
