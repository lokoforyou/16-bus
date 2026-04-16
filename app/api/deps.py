from collections.abc import Generator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.application import ApplicationServices, actor_from_token_data, build_application_services
from app.core.database import clear_database_caches, get_db
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.domain.auth.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def decode_token_to_token_data(token: str | None) -> TokenData | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Could not validate credentials")
        return TokenData(
            user_id=user_id,
            role=payload.get("role"),
            organization_id=payload.get("org_id"),
        )
    except JWTError as exc:
        raise AuthenticationError("Could not validate credentials") from exc


async def get_optional_current_user_token(token: str | None = Depends(oauth2_scheme)) -> TokenData | None:
    return decode_token_to_token_data(token)


async def get_current_user_token(token: str | None = Depends(oauth2_scheme)) -> TokenData:
    token_data = decode_token_to_token_data(token)
    if token_data is None:
        raise AuthenticationError("Could not validate credentials")
    return token_data


def get_application_services(
    db: Session = Depends(get_db),
    token_data: TokenData | None = Depends(get_optional_current_user_token),
) -> ApplicationServices:
    actor = actor_from_token_data(token_data, source="api")
    return build_application_services(session=db, actor=actor, request_source="api")


def reset_dependency_state() -> None:
    clear_database_caches()
