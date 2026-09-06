from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.database.models import Department, LineType, MaintenanceStatus


class MaintenanceCreate(BaseModel):
    department: Department
    asset_type: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    track_section_id: int
    location_km: float
    required_duration_minutes: int = Field(gt=0)
    urgency_priority: int = Field(ge=1, le=10)
    power_isolation_required: bool = False
    traffic_block_required: bool = True


class MaintenanceResponse(MaintenanceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: MaintenanceStatus
    allocated_block_id: Optional[int] = None


class BlockResponse(BaseModel):
    id: int
    track_section_id: int
    section_name: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    status: str
    departments: list[str]
    power_cutoff_required: bool
    traffic_halted: bool
    bundled_requests: list[MaintenanceResponse]


class OptimizationResponse(BaseModel):
    status: str
    blocks_created: int
    requests_scheduled: int
    total_requests: int
    unmet_requests: int
    wall_time: float = 0
    message: str


class KpiResponse(BaseModel):
    total_requests: int
    scheduled_requests: int
    optimized_blocks: int
    siloed_blocks: int
    possession_minutes_before: int
    possession_minutes_after: int
    minutes_saved: int
    block_reduction_percent: float
    possession_reduction_percent: float
    integrated_blocks: int
    train_count: int


class TrackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section_name: str
    start_station_code: str
    end_station_code: str
    line_type: LineType
    start_km: float
    end_km: float
    max_permissible_speed: int
