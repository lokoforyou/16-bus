from typing import Optional
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.auth.models import UserORM
from app.domain.auth.repository import UserRepository
from app.domain.auth.schemas import LoginRequest, Token, UserCreate


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def authenticate(self, request: LoginRequest) -> Token:
        user = self.repository.get_by_phone(request.phone)
        if not user:
            raise AuthenticationError("Invalid phone number or password")

        if not verify_password(request.password, user.password_hash):
            raise AuthenticationError("Invalid phone number or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        access_token = create_access_token(
            subject=user.id,
            role=user.role,
            organization_id=user.organization_id
        )
        return Token(access_token=access_token, token_type="bearer")

    def register(self, data: UserCreate) -> UserORM:
        existing_user = self.repository.get_by_phone(data.phone)
        if existing_user:
            raise ConflictError(f"User with phone {data.phone} already exists")

        user = UserORM(
            full_name=data.full_name,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=data.role,
            organization_id=data.organization_id,
            is_active=data.is_active
        )
        return self.repository.create(user)

    def get_user_by_id(self, user_id: str) -> UserORM:
        user = self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user
