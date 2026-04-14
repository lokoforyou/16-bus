import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ShiftStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DriverShiftORM(Base):
    __tablename__ = "driver_shifts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    status: Mapped[ShiftStatus] = mapped_column(String, nullable=False, default=ShiftStatus.ACTIVE)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
