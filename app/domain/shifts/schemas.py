from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.domain.shifts.models import ShiftStatus


class ShiftBase(BaseModel):
    driver_id: str
    vehicle_id: str
    organization_id: str
    status: ShiftStatus = ShiftStatus.ACTIVE


class ShiftCreate(BaseModel):
    driver_id: str
    vehicle_id: str


class Shift(ShiftBase):
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ShiftList(BaseModel):
    items: List[Shift]
