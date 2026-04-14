from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.domain.organizations.models import OrganizationType


class OrganizationBase(BaseModel):
    name: str
    type: OrganizationType
    compliance_status: str = "pending"
    is_active: bool = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[OrganizationType] = None
    compliance_status: Optional[str] = None
    is_active: Optional[bool] = None


class Organization(OrganizationBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationList(BaseModel):
    items: List[Organization]
