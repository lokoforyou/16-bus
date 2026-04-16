from typing import Optional

from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.vehicles.schemas import Vehicle, VehicleCreate, VehicleList, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", response_model=Vehicle)
async def create_vehicle(
    data: VehicleCreate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.vehicles.create(data)


@router.get("", response_model=VehicleList)
async def list_vehicles(
    organization_id: Optional[str] = None,
    services: ApplicationServices = Depends(get_application_services),
) -> VehicleList:
    return VehicleList(items=services.vehicles.list(organization_id))


@router.get("/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(
    vehicle_id: str,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.vehicles.get(vehicle_id)


@router.patch("/{vehicle_id}", response_model=Vehicle)
async def update_vehicle(
    vehicle_id: str,
    data: VehicleUpdate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.vehicles.update(vehicle_id, data)
