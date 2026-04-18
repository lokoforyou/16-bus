from fastapi import APIRouter, Depends, status

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.trips.models import TripStatus
from app.domain.trips.schemas import TripCreate, TripRead, TripUpdate

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
async def create_trip(
    request: TripCreate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.trips.create(request)


@router.get("", response_model=list[TripRead])
async def list_trips(
    route_id: str | None = None,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.trips.list_active(route_id=route_id)


@router.get("/{trip_id}", response_model=TripRead)
async def get_trip(
    trip_id: str,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.trips.get(trip_id)


@router.post("/{trip_id}/transition", response_model=TripRead)
async def transition_trip(
    trip_id: str,
    new_state: TripStatus,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.trips.transition(trip_id, new_state)


@router.get("/admin", response_model=list[TripRead])
async def list_all_trips(
    services: ApplicationServices = Depends(get_application_services),
):
    return services.trips.list_all()


@router.patch("/admin/{trip_id}", response_model=TripRead)
async def update_trip(
    trip_id: str,
    request: TripUpdate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.trips.update(trip_id, request)
