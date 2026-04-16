from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PolicyORM(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    route_id: Mapped[str | None] = mapped_column(ForeignKey("routes.id"), nullable=True, index=True)
    wait_time_sla_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    pickup_grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    cancellation_grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    eta_breach_credit_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    no_show_fee_type: Mapped[str] = mapped_column(String(32), nullable=False, default="flat")
    no_show_fee_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    pricing_rules_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    refund_rules_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
