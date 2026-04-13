from collections.abc import Generator

from app.core.database import get_db


def get_request_context() -> dict[str, str]:
    return {"request_source": "api"}


def get_db_session() -> Generator:
    yield from get_db()
