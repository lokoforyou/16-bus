from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DriverBase(BaseModel):
    organization_id: str
    full_name: str
    phone: str
    licence_number: str
    pdp_verified: bool = False
    is_active: bool = True


class DriverCreate(DriverBase):
    user_id: str


class DriverUpdate(BaseModel):
    organization_id: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    licence_number: Optional[str] = None
    pdp_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class Driver(DriverBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DriverList(BaseModel):
    items: List[Driver]
