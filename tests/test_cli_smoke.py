import json
from pathlib import Path

from app.cli.main import app
from app.cli import session as cli_session
from app.core.database import get_session_factory
from app.core.security import hash_password
from app.domain.auth.models import UserORM, UserRole
from app.domain.organizations.models import OrganizationORM, OrganizationType
from typer.testing import CliRunner

runner = CliRunner()


def test_busctl_system_health_supports_json() -> None:
    result = runner.invoke(app, ["system", "health", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"


def test_busctl_login_persists_session_and_whoami(monkeypatch) -> None:
    session = get_session_factory()()
    try:
        session.add(OrganizationORM(id="org-cli", name="CLI Org", type=OrganizationType.TAXI_ASSOCIATION))
        session.add(
            UserORM(
                id="user-cli-admin",
                full_name="CLI Admin",
                phone="27020000001",
                password_hash=hash_password("pass123"),
                role=UserRole.ORG_ADMIN,
                organization_id="org-cli",
            )
        )
        session.commit()
    finally:
        session.close()

    temp_session_path = Path("test_busctl_session.json")
    monkeypatch.setattr(cli_session, "SESSION_PATH", temp_session_path)

    login = runner.invoke(
        app,
        ["auth", "login", "--phone", "27020000001", "--password", "pass123", "--json"],
    )
    assert login.exit_code == 0
    assert temp_session_path.exists()

    whoami = runner.invoke(app, ["auth", "whoami", "--json"])
    assert whoami.exit_code == 0
    payload = json.loads(whoami.stdout)
    assert payload["id"] == "user-cli-admin"
    assert payload["organization_id"] == "org-cli"
