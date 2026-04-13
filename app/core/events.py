from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class DomainEvent:
    name: str
    payload: dict[str, Any]
    emitted_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def emit_event(event: DomainEvent) -> DomainEvent:
    """Placeholder for a future event bus or durable outbox implementation."""
    return event
