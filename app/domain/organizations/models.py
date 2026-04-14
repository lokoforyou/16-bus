import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OrganizationType(str, Enum):
    TAXI_ASSOCIATION = "taxi_association"
    PRIVATE_OPERATOR = "private_operator"
    GOVERNMENT = "government"


class OrganizationORM(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    type: Mapped[OrganizationType] = mapped_column(String, nullable=False, default=OrganizationType.TAXI_ASSOCIATION)
    compliance_status: Mapped[str] = mapped_column(String, default="pending")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
