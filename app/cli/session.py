import json
from dataclasses import dataclass
from pathlib import Path

from app.api.deps import decode_token_to_token_data
from app.application.context import Actor, actor_from_token_data
from app.core.exceptions import AuthenticationError

SESSION_PATH = Path(".busctl") / "session.json"


@dataclass(slots=True)
class CliSession:
    access_token: str
    user_id: str
    role: str | None
    organization_id: str | None

    @property
    def actor(self) -> Actor:
        token_data = decode_token_to_token_data(self.access_token)
        actor = actor_from_token_data(token_data, source="cli")
        if actor is None:
            raise AuthenticationError("Invalid CLI session")
        return actor


def save_session(access_token: str) -> CliSession:
    token_data = decode_token_to_token_data(access_token)
    if token_data is None or token_data.user_id is None:
        raise AuthenticationError("Invalid CLI session")
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "access_token": access_token,
        "user_id": token_data.user_id,
        "role": token_data.role.value if token_data.role else None,
        "organization_id": token_data.organization_id,
    }
    SESSION_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return CliSession(**payload)


def load_session(required: bool = True) -> CliSession | None:
    if not SESSION_PATH.exists():
        if required:
            raise AuthenticationError("No active busctl session. Run `busctl auth login`.")
        return None
    payload = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
    return CliSession(**payload)


def clear_session() -> None:
    if SESSION_PATH.exists():
        SESSION_PATH.unlink()
