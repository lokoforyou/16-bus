import asyncio
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


def _topics_for_event(event: DomainEvent) -> list[str]:
    topics = [f"event:{event.name}"]
    if booking_id := event.payload.get("booking_id"):
        topics.append(f"booking:{booking_id}")
    if trip_id := event.payload.get("trip_id"):
        topics.append(f"trip:{trip_id}")
    if shift_id := event.payload.get("shift_id"):
        topics.append(f"shift:{shift_id}")
    return topics


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

    envelope = {
        "name": event.name,
        "payload": event.payload,
        "emitted_at": event.emitted_at.isoformat(),
    }
    for topic in _topics_for_event(event):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(event_channel.publish(topic, envelope))
        except RuntimeError:
            asyncio.run(event_channel.publish(topic, envelope))
    return event
