from app.core.events import DomainEvent, emit_event
from app.core.exceptions import NotFoundError
from app.domain.trips.models import TripORM, TripStatus
from app.domain.trips.repository import TripRepository
from app.domain.trips.schemas import TripCreate
from app.domain.trips.state_machine import validate_transition


class TripService:
    def __init__(self, repository: TripRepository):
        self.repository = repository

    def get_trip(self, trip_id: str) -> TripORM:
        trip = self.repository.get_trip(trip_id)
        if not trip:
            raise NotFoundError("Trip not found")
        return trip

    def list_trips(self, organization_id: str | None = None) -> list[TripORM]:
        return self.repository.list_trips(organization_id=organization_id)

    def transition_trip_state(self, trip_id: str, new_state: TripStatus) -> TripORM:
        trip = self.get_trip(trip_id)
        old_state = trip.state
        validate_transition(old_state, new_state)
        trip.state = new_state.value if isinstance(new_state, TripStatus) else str(new_state)
        updated_trip = self.repository.update(trip)
        emit_event(
            DomainEvent(
                name="trip.state_changed",
                payload={
                    "trip_id": updated_trip.id,
                    "old_state": old_state,
                    "new_state": updated_trip.state,
                    "organization_id": updated_trip.organization_id,
                },
            ),
            session=self.repository.session,
        )
        return updated_trip

    def create_trip(self, trip_data: TripCreate | dict) -> TripORM:
        payload = trip_data.model_dump() if hasattr(trip_data, "model_dump") else dict(trip_data)
        trip = TripORM(**payload)
        created_trip = self.repository.create(trip)
        emit_event(
            DomainEvent(
                name="trip.created",
                payload={
                    "trip_id": created_trip.id,
                    "organization_id": created_trip.organization_id,
                },
            ),
            session=self.repository.session,
        )
        return created_trip
