from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.auth.schemas import User, UserCreate, UserList, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=User)
async def create_user(
    request: UserCreate,
    services: ApplicationServices = Depends(get_application_services),
) -> User:
    return services.users.create_user(request)


@router.get("", response_model=UserList)
async def list_users(
    organization_id: str | None = None,
    services: ApplicationServices = Depends(get_application_services),
) -> UserList:
    return UserList(items=services.users.list_users(organization_id=organization_id))


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> User:
    return services.users.get_user(user_id)


@router.patch("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    request: UserUpdate,
    services: ApplicationServices = Depends(get_application_services),
) -> User:
    return services.users.update_user(user_id, request)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.users.delete_user(user_id)
