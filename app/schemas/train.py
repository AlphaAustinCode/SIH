from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.database.models import LineType


class TrainScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    train_number: str
    train_name: str
    priority_level: int
    track_section_id: int
    scheduled_entry: datetime
    scheduled_exit: datetime
    direction: LineType
