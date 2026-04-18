import asyncio
import inspect
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.audit import record_audit_log
from app.core.database import Base

EventListener = Callable[["DomainEvent"], Any | Awaitable[Any]]
_subscribers: dict[str, list[EventListener]] = defaultdict(list)


class DomainEventRecordORM(Base):
    __tablename__ = "domain_events"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    emitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@dataclass(slots=True)
class DomainEvent:
    name: str
    payload: dict[str, Any]
    emitted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: str = field(default_factory=lambda: f"evt-{uuid4().hex}")


def subscribe(event_name: str, listener: EventListener) -> Callable[[], None]:
    _subscribers[event_name].append(listener)

    def unsubscribe() -> None:
        listeners = _subscribers.get(event_name)
        if not listeners:
            return
        if listener in listeners:
            listeners.remove(listener)
        if not listeners:
            _subscribers.pop(event_name, None)

    return unsubscribe


def _notify_listener(listener: EventListener, event: DomainEvent) -> None:
    result = listener(event)
    if not inspect.isawaitable(result):
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(result)
    else:
        loop.create_task(result)


def publish(event: DomainEvent) -> None:
    listeners = list(_subscribers.get(event.name, [])) + list(_subscribers.get("*", []))
    for listener in listeners:
        _notify_listener(listener, event)


def persist_event(session: Session, event: DomainEvent) -> None:
    session.add(
        DomainEventRecordORM(
            id=event.id,
            name=event.name,
            payload=jsonable_encoder(event.payload),
            emitted_at=event.emitted_at,
        )
    )
    record_audit_log(session, action=event.name, payload=event.payload)
    session.flush()


def emit_event(event: DomainEvent, session: Session | None = None) -> DomainEvent:
    if session is not None:
        persist_event(session, event)
    publish(event)
    return event
