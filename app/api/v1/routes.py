from fastapi import APIRouter, Depends

from app.api.deps import get_route_service, get_current_user_token
from app.domain.auth.models import UserRole
from app.domain.auth.permissions import check_role
from app.domain.auth.schemas import TokenData
from app.domain.routes.schemas import RouteListResponse, RouteStopListResponse, RouteCreate, RouteVariantCreate, RouteStopCreate
from app.domain.routes.service import RouteAdminService

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=RouteListResponse)
async def list_routes(
    route_service: RouteAdminService = Depends(get_route_service),
) -> RouteListResponse:
    return route_service.list_routes()


@router.get("/{route_id}/stops", response_model=RouteStopListResponse)
async def list_route_stops(
    route_id: str,
    route_service: RouteAdminService = Depends(get_route_service),
) -> RouteStopListResponse:
    return route_service.list_route_stops(route_id)


@router.post("")
async def create_route(
    data: RouteCreate,
    route_service: RouteAdminService = Depends(get_route_service),
    token_data: TokenData = Depends(get_current_user_token),
):
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    return route_service.create_route(data)


@router.post("/{route_id}/variants")
async def create_variant(
    route_id: str,
    data: RouteVariantCreate,
    route_service: RouteAdminService = Depends(get_route_service),
    token_data: TokenData = Depends(get_current_user_token),
):
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    return route_service.create_variant(route_id, data)


@router.post("/{route_id}/variants/{variant_id}/stops")
async def add_stop_to_variant(
    route_id: str,
    variant_id: str,
    data: RouteStopCreate,
    route_service: RouteAdminService = Depends(get_route_service),
    token_data: TokenData = Depends(get_current_user_token),
):
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    return route_service.add_stop_to_variant(route_id, variant_id, data)
