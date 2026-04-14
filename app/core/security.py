from datetime import UTC, datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(
    subject: Union[str, Any],
    role: str,
    organization_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    settings = get_settings()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expiry_minutes
        )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "org_id": organization_id,
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
