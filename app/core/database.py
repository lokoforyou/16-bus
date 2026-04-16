from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


def _engine_options(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    database_url = _normalize_database_url(settings.database_url)
    return create_engine(
        database_url,
        pool_pre_ping=True,
        **_engine_options(database_url),
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def import_all_models() -> None:
    import app.core.audit  # noqa: F401
    import app.core.events  # noqa: F401
    import app.domain.auth.models  # noqa: F401
    import app.domain.bookings.models  # noqa: F401
    import app.domain.compliance.models  # noqa: F401
    import app.domain.drivers.models  # noqa: F401
    import app.domain.organizations.models  # noqa: F401
    import app.domain.policies.models  # noqa: F401
    import app.domain.payments.models  # noqa: F401
    import app.domain.qr.models  # noqa: F401
    import app.domain.ranks.models  # noqa: F401
    import app.domain.routes.models  # noqa: F401
    import app.domain.shifts.models  # noqa: F401
    import app.domain.telemetry.models  # noqa: F401
    import app.domain.trips.models  # noqa: F401
    import app.domain.vehicles.models  # noqa: F401


def init_database() -> None:
    import_all_models()
    Base.metadata.create_all(bind=get_engine())


def reset_database() -> None:
    import_all_models()
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())


def clear_database_caches() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
