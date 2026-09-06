from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MaintenanceRequest
from app.schemas.maintenance import MaintenanceRequestCreate, MaintenanceRequestResponse

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

@router.get("/", response_model=List[MaintenanceRequestResponse])
def get_all_maintenance_requests(department: str = None, status: str = None, db: Session = Depends(get_db)):
    query = db.query(MaintenanceRequest)
    if department:
        query = query.filter(MaintenanceRequest.department == department)
    if status:
        query = query.filter(MaintenanceRequest.status == status)
    return query.all()

@router.post("/", response_model=MaintenanceRequestResponse, status_code=201)
def create_maintenance_request(request: MaintenanceRequestCreate, db: Session = Depends(get_db)):
    new_req = MaintenanceRequest(**request.model_dump(), status="PENDING")
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req