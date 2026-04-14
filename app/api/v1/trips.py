from fastapi import APIRouter, Depends

from app.api.deps import get_trip_service, get_current_user_token
from app.domain.auth.models import UserRole
from app.domain.auth.permissions import check_role
from app.domain.auth.schemas import TokenData
from app.domain.trips.models import TripORM, TripStatus
from app.domain.trips.schemas import TripRead
from app.domain.trips.service import TripService

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("/{trip_id}", response_model=TripRead)
async def get_trip(
    trip_id: str,
    trip_service: TripService = Depends(get_trip_service),
) -> TripORM:
    return trip_service.get_trip(trip_id)


@router.post("/{trip_id}/transition", response_model=TripRead)
async def transition_trip(
    trip_id: str,
    new_state: TripStatus,
    trip_service: TripService = Depends(get_trip_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> TripORM:
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.DRIVER])
    return trip_service.transition_trip_state(trip_id, new_state)
