from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_route_service
from app.domain.routes.schemas import RouteListResponse, RouteStopListResponse
from app.domain.routes.service import RouteService

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=RouteListResponse)
async def list_routes(
    route_service: RouteService = Depends(get_route_service),
) -> RouteListResponse:
    return route_service.list_routes()


@router.get("/{route_id}/stops", response_model=RouteStopListResponse)
async def list_route_stops(
    route_id: str,
    route_service: RouteService = Depends(get_route_service),
) -> RouteStopListResponse:
    response = route_service.list_route_stops(route_id)
    if not response.items:
        raise HTTPException(status_code=404, detail="Route not found")
    return response
