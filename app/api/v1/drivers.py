from typing import Optional
from fastapi import APIRouter, Depends
from app.api.deps import get_driver_service, get_current_user_token
from app.domain.auth.models import UserRole
from app.domain.auth.permissions import check_role, check_org_ownership
from app.domain.auth.schemas import TokenData
from app.domain.drivers.models import DriverORM
from app.domain.drivers.schemas import (
    Driver,
    DriverCreate,
    DriverList,
    DriverUpdate,
)
from app.domain.drivers.service import DriverService

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("", response_model=Driver)
async def create_driver(
    data: DriverCreate,
    driver_service: DriverService = Depends(get_driver_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> DriverORM:
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    check_org_ownership(token_data, data.organization_id)
    return driver_service.create_driver(data)


@router.get("", response_model=DriverList)
async def list_drivers(
    organization_id: Optional[str] = None,
    driver_service: DriverService = Depends(get_driver_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> DriverList:
    if organization_id:
        check_org_ownership(token_data, organization_id)
    elif token_data.role != UserRole.SUPER_ADMIN:
        organization_id = token_data.organization_id
        
    items = driver_service.list_drivers(organization_id)
    return DriverList(items=items)


@router.get("/{driver_id}", response_model=Driver)
async def get_driver(
    driver_id: str,
    driver_service: DriverService = Depends(get_driver_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> DriverORM:
    driver = driver_service.get_driver(driver_id)
    check_org_ownership(token_data, driver.organization_id)
    return driver


@router.patch("/{driver_id}", response_model=Driver)
async def update_driver(
    driver_id: str,
    data: DriverUpdate,
    driver_service: DriverService = Depends(get_driver_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> DriverORM:
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    driver = driver_service.get_driver(driver_id)
    check_org_ownership(token_data, driver.organization_id)
    
    if data.organization_id:
        check_org_ownership(token_data, data.organization_id)
        
    return driver_service.update_driver(driver_id, data)
