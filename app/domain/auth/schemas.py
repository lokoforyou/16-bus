from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.domain.auth.models import UserRole


class UserBase(BaseModel):
    full_name: str
    phone: str
    role: UserRole
    organization_id: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    organization_id: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[UserRole] = None
    organization_id: Optional[str] = None


class LoginRequest(BaseModel):
    phone: str
    password: str
