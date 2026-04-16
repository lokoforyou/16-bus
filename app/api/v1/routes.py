from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.routes.schemas import (
    RouteCreate,
    RouteListResponse,
    RouteStopCreate,
    RouteStopListResponse,
    RouteVariantCreate,
)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=RouteListResponse)
async def list_routes(
    services: ApplicationServices = Depends(get_application_services),
) -> RouteListResponse:
    return services.routes.list()


@router.get("/{route_id}/stops", response_model=RouteStopListResponse)
async def list_route_stops(
    route_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> RouteStopListResponse:
    return services.routes.list_route_stops(route_id)


@router.post("")
async def create_route(
    data: RouteCreate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.routes.create(data)


@router.post("/{route_id}/variants")
async def create_variant(
    route_id: str,
    data: RouteVariantCreate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.routes.create_variant(route_id, data)


@router.post("/{route_id}/variants/{variant_id}/stops")
async def add_stop_to_variant(
    route_id: str,
    variant_id: str,
    data: RouteStopCreate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.routes.add_stop_to_variant(route_id, variant_id, data)
