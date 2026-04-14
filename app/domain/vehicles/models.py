import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VehicleORM(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    plate_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=16)
    permit_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    compliance_status: Mapped[str] = mapped_column(String, default="pending")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
