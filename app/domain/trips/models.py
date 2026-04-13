from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TripORM(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    route_id: Mapped[str] = mapped_column(ForeignKey("routes.id"), nullable=False, index=True)
    route_variant_id: Mapped[str] = mapped_column(
        ForeignKey("route_variants.id"), nullable=False, index=True
    )
    organization_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    driver_id: Mapped[str] = mapped_column(String(64), nullable=False)
    trip_type: Mapped[str] = mapped_column(String(32), nullable=False)
    planned_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    seats_total: Mapped[int] = mapped_column(Integer, nullable=False)
    seats_free: Mapped[int] = mapped_column(Integer, nullable=False)
    current_stop_id: Mapped[str] = mapped_column(ForeignKey("stops.id"), nullable=False)
