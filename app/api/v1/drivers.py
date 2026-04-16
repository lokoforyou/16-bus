from typing import Optional

from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.drivers.schemas import Driver, DriverCreate, DriverList, DriverUpdate

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("", response_model=Driver)
async def create_driver(
    data: DriverCreate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.drivers.create(data)


@router.get("", response_model=DriverList)
async def list_drivers(
    organization_id: Optional[str] = None,
    services: ApplicationServices = Depends(get_application_services),
) -> DriverList:
    return DriverList(items=services.drivers.list(organization_id))


@router.get("/{driver_id}", response_model=Driver)
async def get_driver(
    driver_id: str,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.drivers.get(driver_id)


@router.patch("/{driver_id}", response_model=Driver)
async def update_driver(
    driver_id: str,
    data: DriverUpdate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.drivers.update(driver_id, data)
