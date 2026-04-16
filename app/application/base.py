from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session

from app.application.context import Actor

T = TypeVar("T")


class ApplicationService:
    def __init__(self, session: Session, actor: Actor | None, request_source: str = "api") -> None:
        self.session = session
        self.actor = actor
        self.request_source = request_source

    def transact(self, operation: Callable[[], T]) -> T:
        try:
            result = operation()
            self.session.commit()
            return result
        except Exception:
            self.session.rollback()
            raise
