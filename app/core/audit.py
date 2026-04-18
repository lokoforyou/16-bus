from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base


class AuditLogORM(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    action: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def _extract_entity_id(payload: dict[str, Any]) -> str | None:
    for key in (
        "entity_id",
        "booking_id",
        "trip_id",
        "payment_id",
        "shift_id",
        "qr_token_id",
        "driver_id",
        "vehicle_id",
        "route_id",
        "organization_id",
        "user_id",
    ):
        value = payload.get(key)
        if value:
            return str(value)
    return None


def record_audit_log(
    session: Session,
    *,
    action: str,
    payload: dict[str, Any],
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor_id: str | None = None,
) -> AuditLogORM:
    inferred_entity_type = entity_type or action.split(".", 1)[0]
    inferred_entity_id = entity_id or _extract_entity_id(payload)
    encoded_payload = jsonable_encoder(payload)
    record = AuditLogORM(
        id=f"audit-{uuid4().hex}",
        action=action,
        entity_type=inferred_entity_type,
        entity_id=inferred_entity_id,
        actor_id=actor_id,
        payload=encoded_payload,
        recorded_at=datetime.now(UTC),
    )
    session.add(record)
    session.flush()
    return record
