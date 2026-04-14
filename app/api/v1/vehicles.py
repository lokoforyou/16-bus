from typing import Optional
from fastapi import APIRouter, Depends
from app.api.deps import get_vehicle_service, get_current_user_token
from app.domain.auth.models import UserRole
from app.domain.auth.permissions import check_role, check_org_ownership
from app.domain.auth.schemas import TokenData
from app.domain.vehicles.models import VehicleORM
from app.domain.vehicles.schemas import (
    Vehicle,
    VehicleCreate,
    VehicleList,
    VehicleUpdate,
)
from app.domain.vehicles.service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", response_model=Vehicle)
async def create_vehicle(
    data: VehicleCreate,
    vehicle_service: VehicleService = Depends(get_vehicle_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> VehicleORM:
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    check_org_ownership(token_data, data.organization_id)
    return vehicle_service.create_vehicle(data)


@router.get("", response_model=VehicleList)
async def list_vehicles(
    organization_id: Optional[str] = None,
    vehicle_service: VehicleService = Depends(get_vehicle_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> VehicleList:
    # If org_id provided, check ownership
    if organization_id:
        check_org_ownership(token_data, organization_id)
    elif token_data.role != UserRole.SUPER_ADMIN:
        # Regular org admins only see their own by default
        organization_id = token_data.organization_id
        
    items = vehicle_service.list_vehicles(organization_id)
    return VehicleList(items=items)


@router.get("/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(
    vehicle_id: str,
    vehicle_service: VehicleService = Depends(get_vehicle_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> VehicleORM:
    vehicle = vehicle_service.get_vehicle(vehicle_id)
    check_org_ownership(token_data, vehicle.organization_id)
    return vehicle


@router.patch("/{vehicle_id}", response_model=Vehicle)
async def update_vehicle(
    vehicle_id: str,
    data: VehicleUpdate,
    vehicle_service: VehicleService = Depends(get_vehicle_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> VehicleORM:
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    vehicle = vehicle_service.get_vehicle(vehicle_id)
    check_org_ownership(token_data, vehicle.organization_id)
    
    if data.organization_id:
        check_org_ownership(token_data, data.organization_id)
        
    return vehicle_service.update_vehicle(vehicle_id, data)
