import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DriverORM(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    licence_number: Mapped[str] = mapped_column(String, nullable=False)
    pdp_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
