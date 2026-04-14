from typing import List
from app.core.exceptions import PermissionDeniedError
from app.domain.auth.models import UserRole
from app.domain.auth.schemas import TokenData


def check_role(token_data: TokenData, allowed_roles: List[UserRole]):
    if token_data.role not in allowed_roles:
        raise PermissionDeniedError(
            f"Required role: {', '.join(allowed_roles)}. Your role: {token_data.role}"
        )


def check_org_ownership(token_data: TokenData, organization_id: str):
    if token_data.role == UserRole.SUPER_ADMIN:
        return
    if token_data.organization_id != organization_id:
        raise PermissionDeniedError("You do not have access to this organization")
