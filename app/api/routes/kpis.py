from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.models import AllocatedBlock, MaintenanceRequest, TrainSchedule
from app.database.session import get_db
from app.schemas.api import KpiResponse

router = APIRouter(prefix="/api/kpis", tags=["kpis"])


@router.get("", response_model=KpiResponse)
def get_kpis(db: Session = Depends(get_db)):
    requests = db.query(MaintenanceRequest).all()
    blocks = db.query(AllocatedBlock).all()
    before = sum(item.required_duration_minutes for item in requests)
    after = sum(
        int((block.end_time - block.start_time).total_seconds() / 60)
        for block in blocks
    )
    scheduled = sum(len(block.maintenance_requests) for block in blocks)
    integrated = sum(len(block.maintenance_requests) > 1 for block in blocks)
    saved = before - after
    return KpiResponse(
        total_requests=len(requests),
        scheduled_requests=scheduled,
        optimized_blocks=len(blocks),
        siloed_blocks=len(requests),
        possession_minutes_before=before,
        possession_minutes_after=after,
        minutes_saved=saved,
        block_reduction_percent=(max(0, len(requests) - len(blocks)) / len(requests) * 100)
        if requests else 0,
        possession_reduction_percent=(saved / before * 100) if before else 0,
        integrated_blocks=integrated,
        train_count=db.query(TrainSchedule).count(),
    )
