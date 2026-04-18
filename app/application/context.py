from dataclasses import dataclass

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.domain.auth.models import UserRole
from app.domain.auth.schemas import TokenData
from typing import List


@dataclass(slots=True)
class Actor:
    user_id: str | None = None
    role: UserRole | None = None
    organization_id: str | None = None
    source: str = "system"

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None


def actor_from_token_data(token_data: TokenData | None, source: str = "api") -> Actor | None:
    if token_data is None or token_data.user_id is None:
        return None
    return Actor(
        user_id=token_data.user_id,
        role=token_data.role,
        organization_id=token_data.organization_id,
        source=source,
    )


def require_authenticated(actor: Actor | None) -> Actor:
    if actor is None or not actor.is_authenticated:
        raise AuthenticationError("Authentication required")
    return actor


def require_roles(actor: Actor | None, allowed_roles: List[UserRole]) -> Actor:
    current_actor = require_authenticated(actor)
    if current_actor.role not in allowed_roles:
        raise PermissionDeniedError(
            f"Required role: {', '.join(role.value for role in allowed_roles)}. "
            f"Your role: {current_actor.role}"
        )
    return current_actor


def require_org_access(actor: Actor | None, organization_id: str) -> Actor:
    current_actor = require_authenticated(actor)
    if current_actor.role == UserRole.SUPER_ADMIN:
        return current_actor
    if current_actor.organization_id != organization_id:
        raise PermissionDeniedError("You do not have access to this organization")
    return current_actor
