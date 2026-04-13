from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_trip_service
from app.domain.trips.schemas import TripRead
from app.domain.trips.service import TripService

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("/{trip_id}", response_model=TripRead)
async def get_trip(
    trip_id: str,
    trip_service: TripService = Depends(get_trip_service),
) -> TripRead:
    trip = trip_service.get_trip(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip
