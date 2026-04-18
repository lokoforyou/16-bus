from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.auth.schemas import LoginRequest, Token, User, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest,
    services: ApplicationServices = Depends(get_application_services),
) -> Token:
    return services.auth.login(request)


@router.get("/me", response_model=User)
async def get_me(
    services: ApplicationServices = Depends(get_application_services),
):
    return services.auth.get_current_user()


@router.post("/register", response_model=User)
async def register(
    request: UserCreate,
    services: ApplicationServices = Depends(get_application_services),
) -> User:
    return services.auth.register(request)
