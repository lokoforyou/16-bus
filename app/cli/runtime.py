from collections.abc import Iterator
from contextlib import contextmanager

from app.application import build_application_services
from app.application.context import Actor
from app.core.database import get_session_factory


@contextmanager
def application_services(actor: Actor | None = None) -> Iterator:
    session = get_session_factory()()
    try:
        yield build_application_services(session=session, actor=actor, request_source="cli")
    finally:
        session.close()
