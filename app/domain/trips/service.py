from app.domain.trips.repository import TripRepository
from app.domain.trips.schemas import TripRead


class TripService:
    def __init__(self, repository: TripRepository) -> None:
        self.repository = repository

    def get_trip(self, trip_id: str) -> TripRead | None:
        trip = self.repository.get_trip(trip_id)
        return TripRead.model_validate(trip) if trip else None
