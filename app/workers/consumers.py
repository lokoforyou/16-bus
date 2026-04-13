from app.core.events import DomainEvent
from app.workers.tasks import handle_event


def consume(event: DomainEvent) -> dict[str, str]:
    return handle_event(event)
