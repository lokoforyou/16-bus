import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_session_factory


@dataclass(slots=True)
class DomainEvent:
    name: str
    payload: dict[str, Any]
    emitted_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryEventChannel:
    def __init__(self) -> None:
        self._listeners: dict[str, list] = {}

    def subscribe(self, topic: str, callback) -> None:
        self._listeners.setdefault(topic, []).append(callback)

    def unsubscribe(self, topic: str, callback) -> None:
        callbacks = self._listeners.get(topic, [])
        if callback in callbacks:
            callbacks.remove(callback)

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        for callback in list(self._listeners.get(topic, [])):
            await callback(payload)


event_channel = InMemoryEventChannel()


def emit_event(event: DomainEvent, session: Session | None = None) -> DomainEvent:
    owns_session = session is None
    db = session or get_session_factory()()
    try:
        db.execute(
            text(
                """
                INSERT INTO domain_events (id, name, payload, emitted_at)
                VALUES (:id, :name, :payload, :emitted_at)
                """
            ),
            {
                "id": f"evt-{uuid4().hex}",
                "name": event.name,
                "payload": json.dumps(event.payload),
                "emitted_at": event.emitted_at,
            },
        )
        if owns_session:
            db.commit()
    finally:
        if owns_session:
            db.close()
    return event
