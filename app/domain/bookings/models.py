from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BookingStatus(str, Enum):
    HELD = "held"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    BOARDED = "boarded"


class BookingORM(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id"), nullable=False, index=True)
    passenger_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    origin_stop_id: Mapped[str] = mapped_column(ForeignKey("stops.id"), nullable=False)
    destination_stop_id: Mapped[str] = mapped_column(ForeignKey("stops.id"), nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    fare_amount: Mapped[float] = mapped_column(Float, nullable=False)
    hold_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False)
    booking_state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    forfeiture_fee_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    booking_channel: Mapped[str] = mapped_column(String(32), nullable=False)
    qr_token_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
