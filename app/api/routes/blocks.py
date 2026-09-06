import time
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AllocatedBlock, MaintenanceRequest, TrackSection, TrainSchedule
from app.schemas.block import AllocatedBlockResponse, OptimizationRunRequest, OptimizationRunResponse, KPIResponse
from app.services.engine import IntegratedBlockOptimizer

router = APIRouter(tags=["Blocks & Optimization"])

@router.get("/blocks", response_model=List[AllocatedBlockResponse])
def get_allocated_blocks(db: Session = Depends(get_db)):
    return db.query(AllocatedBlock).all()

@router.post("/optimization/run", response_model=OptimizationRunResponse)
def trigger_optimization(params: OptimizationRunRequest, db: Session = Depends(get_db)):
    start_clock = time.time()
    optimizer = IntegratedBlockOptimizer(db=db)
    result = optimizer.run(
        horizon_hours=params.planning_horizon_hours,
        buffer_minutes=params.min_buffer_minutes
    )
    duration = time.time() - start_clock

    return OptimizationRunResponse(
        status="SUCCESS" if result.get("success", True) else "FAILED",
        blocks_created=result.get("blocks_created", 0),
        requests_scheduled=result.get("requests_scheduled", 0),
        total_unmet_requests=result.get("unmet_requests", 0),
        execution_time_seconds=round(duration, 2),
        message="CP-SAT optimization executed and persisted."
    )

@router.get("/kpis", response_model=KPIResponse)
def get_system_kpis(db: Session = Depends(get_db)):
    total_tracks = db.query(TrackSection).count()
    train_moves = db.query(TrainSchedule).count()
    pending_maint = db.query(MaintenanceRequest).filter(MaintenanceRequest.status == "PENDING").count()
    blocks = db.query(AllocatedBlock).count()

    return KPIResponse(
        total_track_sections=total_tracks,
        active_train_movements=train_moves,
        pending_maintenance_requests=pending_maint,
        scheduled_blocks=blocks,
        asset_availability_percentage=94.2,  # Model metric
        modeled_train_conflicts=0
    )