from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TrainScheduleBase(BaseModel):
    train_number: str
    train_name: str
    priority: int
    section_code: str
    entry_time: datetime
    exit_time: datetime

class TrainScheduleResponse(TrainScheduleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)