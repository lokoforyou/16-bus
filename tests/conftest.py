import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from alembic import command
from alembic.config import Config

os.environ["16_BUS_SUPABASE_URL"] = "sqlite:///./test_16_bus.db"

from app.core.config import get_settings
from app.core.database import clear_database_caches
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_app_state() -> None:
    get_settings.cache_clear()
    clear_database_caches()
    db_file = Path("test_16_bus.db")
    if db_file.exists():
        db_file.unlink()
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")
    yield
    clear_database_caches()
    if db_file.exists():
        db_file.unlink()


@pytest.fixture
def client() -> TestClient:
    with TestClient(create_app()) as test_client:
        yield test_client
