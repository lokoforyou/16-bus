from app.core.events import DomainEvent


def handle_event(event: DomainEvent) -> dict[str, str]:
    return {"event": event.name, "status": "accepted"}
