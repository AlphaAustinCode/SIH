from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database.models import AllocatedBlock, MaintenanceRequest
from app.database.session import get_db
from app.schemas.api import BlockResponse, OptimizationResponse
from app.services.block_service import block_response
from app.services.engine import IntegratedBlockOptimizer

router = APIRouter(prefix="/api/optimization", tags=["optimization"])


@router.post("/run", response_model=OptimizationResponse)
def run_optimization(db: Session = Depends(get_db)):
    total_requests = db.query(MaintenanceRequest).count()
    result = IntegratedBlockOptimizer(db=db).optimize()
    scheduled = result.get("scheduled_count", 0)
    status = result.get("status", "UNKNOWN")
    return OptimizationResponse(
        status=status,
        blocks_created=result.get("blocks_created", 0),
        requests_scheduled=scheduled,
        total_requests=total_requests,
        unmet_requests=max(0, total_requests - scheduled),
        wall_time=result.get("wall_time", 0),
        message=f"Optimization completed with status {status}.",
    )


@router.get("/latest", response_model=list[BlockResponse])
def latest_optimization(db: Session = Depends(get_db)):
    blocks = (
        db.query(AllocatedBlock)
        .options(
            joinedload(AllocatedBlock.track_section),
            joinedload(AllocatedBlock.maintenance_requests),
        )
        .order_by(AllocatedBlock.start_time)
        .all()
    )
    return [block_response(block) for block in blocks]
