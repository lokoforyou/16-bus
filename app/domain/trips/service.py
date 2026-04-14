from datetime import datetime
from typing import Optional
from app.core.exceptions import NotFoundError
from app.domain.trips.models import TripORM, TripStatus
from app.domain.trips.repository import TripRepository
from app.domain.trips.state_machine import validate_transition

class TripService:
    def __init__(self, repository: TripRepository):
        self.repository = repository

    def get_trip(self, trip_id: str) -> TripORM:
        trip = self.repository.get_trip(trip_id)
        if not trip:
            raise NotFoundError("Trip not found")
        return trip

    def transition_trip_state(self, trip_id: str, new_state: TripStatus) -> TripORM:
        trip = self.get_trip(trip_id)
        validate_transition(trip.state, new_state)
        
        trip.state = new_state
        if new_state == TripStatus.COMPLETED:
            trip.actual_end_time = datetime.now()
        
        return self.repository.update(trip)

    def create_trip(self, trip_data: dict) -> TripORM:
        # TODO: Add validation logic here
        trip = TripORM(**trip_data)
        return self.repository.create(trip)
