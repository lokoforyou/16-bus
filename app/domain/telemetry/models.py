import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Float, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class VehicleLocationORM(Base):
    __tablename__ = "vehicle_locations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
