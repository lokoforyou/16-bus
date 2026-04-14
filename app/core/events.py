from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, Dict, List

# Simple in-memory pub/sub system
_subscribers: Dict[str, List[Callable]] = defaultdict(list)

def subscribe(event_name: str, listener: Callable):
    """Subscribes a listener to a specific event."""
    _subscribers[event_name].append(listener)

def publish(event: 'DomainEvent'):
    """Publishes an event to all registered subscribers."""
    for listener in _subscribers[event.name]:
        try:
            listener(event)
        except Exception as e:
            # Log error but continue publishing to other listeners
            print(f"Error notifying subscriber for event {event.name}: {e}")

@dataclass(slots=True)
class DomainEvent:
    name: str
    payload: dict[str, Any]
    emitted_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def emit_event(event: DomainEvent) -> DomainEvent:
    """Publishes a domain event."""
    publish(event)
    return event
