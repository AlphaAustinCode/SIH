from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.maintenance import MaintenanceRequestResponse

class AllocatedBlockBase(BaseModel):
    section_code: str
    start_time: datetime
    end_time: datetime
    status: str
    power_cutoff_required: bool
    traffic_halted: bool

class AllocatedBlockResponse(AllocatedBlockBase):
    id: int
    duration_minutes: int
    bundled_requests: List[MaintenanceRequestResponse] = []
    model_config = ConfigDict(from_attributes=True)

class OptimizationRunRequest(BaseModel):
    planning_horizon_hours: int = 24
    min_buffer_minutes: int = 5

class OptimizationRunResponse(BaseModel):
    status: str
    blocks_created: int
    requests_scheduled: int
    total_unmet_requests: int
    execution_time_seconds: float
    message: str

class KPIResponse(BaseModel):
    total_track_sections: int
    active_train_movements: int
    pending_maintenance_requests: int
    scheduled_blocks: int
    asset_availability_percentage: float
    modeled_train_conflicts: int