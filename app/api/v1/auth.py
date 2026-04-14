from fastapi import APIRouter, Depends
from app.api.deps import get_auth_service, get_current_user
from app.domain.auth.models import UserORM
from app.domain.auth.schemas import LoginRequest, Token, User
from app.domain.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    return auth_service.authenticate(request)


@router.get("/me", response_model=User)
async def get_me(
    current_user: UserORM = Depends(get_current_user),
) -> UserORM:
    return current_user
