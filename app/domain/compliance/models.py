import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class BoardingORM(Base):
    __tablename__ = "boardings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id: Mapped[str] = mapped_column(String, ForeignKey("bookings.id"), index=True, nullable=False)
    driver_id: Mapped[str] = mapped_column(String, ForeignKey("drivers.id"), index=True, nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String, ForeignKey("vehicles.id"), index=True, nullable=False)
    stop_id: Mapped[str] = mapped_column(String, ForeignKey("stops.id"), index=True, nullable=False)
    boarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
