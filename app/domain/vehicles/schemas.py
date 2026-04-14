from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class VehicleBase(BaseModel):
    organization_id: str
    plate_number: str
    capacity: int = 16
    permit_number: Optional[str] = None
    compliance_status: str = "pending"
    is_active: bool = True


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    organization_id: Optional[str] = None
    plate_number: Optional[str] = None
    capacity: Optional[int] = None
    permit_number: Optional[str] = None
    compliance_status: Optional[str] = None
    is_active: Optional[bool] = None


class Vehicle(VehicleBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleList(BaseModel):
    items: List[Vehicle]
