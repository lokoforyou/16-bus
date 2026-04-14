from datetime import datetime
from typing import Optional
from app.core.exceptions import NotFoundError
from app.domain.trips.models import TripORM, TripStatus
from app.domain.trips.repository import TripRepository
from app.domain.trips.state_machine import validate_transition
from app.core.events import emit_event, DomainEvent

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
        
        updated_trip = self.repository.update(trip)

        # Emit event for state change
        emit_event(
            DomainEvent(
                name="trip_state_changed",
                payload={
                    "trip_id": updated_trip.id,
                    "old_state": trip.state, # Use the state before update
                    "new_state": updated_trip.state,
                    "trip_details": updated_trip.model_dump(), # Or relevant subset
                },
            )
        )
        return updated_trip

    def create_trip(self, trip_data: dict) -> TripORM:
        # TODO: Add validation logic here
        trip = TripORM(**trip_data)
        created_trip = self.repository.create(trip)

        # Emit event for trip creation
        emit_event(
            DomainEvent(
                name="trip_created",
                payload={
                    "trip_id": created_trip.id,
                    "trip_details": created_trip.model_dump(), # Or relevant subset
                },
            )
        )
        return created_trip

