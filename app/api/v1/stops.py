from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.routes.schemas import StopCreate, StopListResponse, StopRead, StopUpdate

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("", response_model=StopListResponse)
async def list_stops(
    active_only: bool = False,
    services: ApplicationServices = Depends(get_application_services),
) -> StopListResponse:
    return services.stops.list(active_only=active_only)


@router.get("/{stop_id}", response_model=StopRead)
async def get_stop(
    stop_id: str,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.stops.get(stop_id)


@router.post("", response_model=StopRead)
async def create_stop(
    data: StopCreate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.stops.create(data)


@router.patch("/{stop_id}", response_model=StopRead)
async def update_stop(
    stop_id: str,
    data: StopUpdate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.stops.update(stop_id, data)


@router.delete("/{stop_id}")
async def delete_stop(
    stop_id: str,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.stops.delete(stop_id)
