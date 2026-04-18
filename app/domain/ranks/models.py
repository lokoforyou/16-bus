from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RankQueueState(str, Enum):
    ISSUED = "issued"
    ASSIGNED = "assigned"
    BOARDED = "boarded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class RankQueueTicketORM(Base):
    __tablename__ = "rank_queue_tickets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rank_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trip_id: Mapped[str | None] = mapped_column(ForeignKey("trips.id"), nullable=True, index=True)
    queue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False)
    qr_token_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
