from typing import Optional
from pydantic import BaseModel, ConfigDict

class MaintenanceRequestBase(BaseModel):
    request_id: str
    department: str
    asset_type: str
    section_code: str
    start_km: float
    end_km: float
    duration_minutes: int
    urgency: int
    requires_power_block: bool
    requires_traffic_block: bool

class MaintenanceRequestCreate(MaintenanceRequestBase):
    pass

class MaintenanceRequestResponse(MaintenanceRequestBase):
    id: int
    status: str
    allocated_block_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)