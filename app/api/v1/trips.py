from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user_token, get_trip_service
from app.domain.auth.models import UserRole
from app.domain.auth.permissions import check_org_ownership, check_role
from app.domain.auth.schemas import TokenData
from app.domain.trips.models import TripORM, TripStatus
from app.domain.trips.schemas import TripCreate, TripRead
from app.domain.trips.service import TripService

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
async def create_trip(
    request: TripCreate,
    trip_service: TripService = Depends(get_trip_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> TripORM:
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    check_org_ownership(token_data, request.organization_id)
    return trip_service.create_trip(request)


@router.get("/{trip_id}", response_model=TripRead)
async def get_trip(
    trip_id: str,
    trip_service: TripService = Depends(get_trip_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> TripORM:
    trip = trip_service.get_trip(trip_id)
    check_org_ownership(token_data, trip.organization_id)
    return trip


@router.post("/{trip_id}/transition", response_model=TripRead)
async def transition_trip(
    trip_id: str,
    new_state: TripStatus,
    trip_service: TripService = Depends(get_trip_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> TripORM:
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.DRIVER])
    trip = trip_service.get_trip(trip_id)
    check_org_ownership(token_data, trip.organization_id)
    return trip_service.transition_trip_state(trip_id, new_state)
