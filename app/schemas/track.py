from typing import Optional
from pydantic import BaseModel, ConfigDict

class TrackSectionBase(BaseModel):
    section_code: str
    station_from: str
    station_to: str
    line_type: str
    start_km: float
    end_km: float
    max_permissible_speed: int

class TrackSectionResponse(TrackSectionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)