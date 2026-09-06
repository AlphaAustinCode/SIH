from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database.models import AllocatedBlock
from app.database.session import get_db
from app.schemas.api import BlockResponse
from app.services.block_service import block_response

router = APIRouter(prefix="/api/blocks", tags=["blocks"])


@router.get("", response_model=list[BlockResponse])
def list_blocks(db: Session = Depends(get_db)):
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


@router.get("/{block_id}", response_model=BlockResponse)
def get_block(block_id: int, db: Session = Depends(get_db)):
    block = (
        db.query(AllocatedBlock)
        .options(
            joinedload(AllocatedBlock.track_section),
            joinedload(AllocatedBlock.maintenance_requests),
        )
        .filter(AllocatedBlock.id == block_id)
        .first()
    )
    if block is None:
        raise HTTPException(status_code=404, detail="Allocated block not found")
    return block_response(block)
