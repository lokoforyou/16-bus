from app.core.events import DomainEvent, emit_event
from app.core.exceptions import DomainRuleViolationError, NotFoundError
from app.domain.events import DomainEventName
from app.domain.routes.repository import RouteRepository
from app.domain.drivers.repository import DriverRepository
from app.domain.vehicles.repository import VehicleRepository
from app.domain.trips.models import TripORM, TripStatus
from app.domain.trips.repository import TripRepository
from app.domain.trips.schemas import TripCreate, TripUpdate
from app.domain.trips.state_machine import validate_transition


class TripService:
    def __init__(
        self,
        repository: TripRepository,
        route_repository: RouteRepository,
        driver_repository: DriverRepository,
        vehicle_repository: VehicleRepository,
    ):
        self.repository = repository
        self.route_repository = route_repository
        self.driver_repository = driver_repository
        self.vehicle_repository = vehicle_repository

    def get_trip(self, trip_id: str) -> TripORM:
        trip = self.repository.get_trip(trip_id)
        if not trip:
            raise NotFoundError("Trip not found")
        return trip

    def list_trips(self, organization_id: str | None = None) -> list[TripORM]:
        return self.repository.list_trips(organization_id=organization_id)

    def update_trip(self, trip_id: str, data: TripUpdate | dict) -> TripORM:
        trip = self.get_trip(trip_id)
        payload = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else dict(data)
        old_state = trip.state

        route_id = payload.get("route_id", trip.route_id)
        route_variant_id = payload.get("route_variant_id", trip.route_variant_id)
        organization_id = payload.get("organization_id", trip.organization_id)
        vehicle_id = payload.get("vehicle_id", trip.vehicle_id)
        driver_id = payload.get("driver_id", trip.driver_id)

        route = self.route_repository.get_route(route_id)
        if route is None:
            raise NotFoundError("Route not found")
        variant = self.route_repository.get_variant(route_variant_id)
        if variant is None or variant.route_id != route.id:
            raise DomainRuleViolationError("Route variant does not belong to the route")

        vehicle = self.vehicle_repository.get_by_id(vehicle_id)
        if vehicle is None:
            raise NotFoundError("Vehicle not found")
        if vehicle.organization_id != organization_id or route.organization_id != organization_id:
            raise DomainRuleViolationError("Trip organization must match route and vehicle organization")

        driver = self.driver_repository.get_by_id(driver_id)
        if driver is None:
            raise NotFoundError("Driver not found")
        if driver.organization_id != organization_id:
            raise DomainRuleViolationError("Trip driver must belong to the same organization")

        if "state" in payload and payload["state"] != trip.state:
            validate_transition(trip.state, TripStatus(payload["state"]))

        for field, value in payload.items():
            setattr(trip, field, value)

        if trip.seats_free > trip.seats_total:
            raise DomainRuleViolationError("Seats free cannot exceed seats total")

        updated_trip = self.repository.update(trip)
        emit_event(
            DomainEvent(
                name=DomainEventName.TRIP_STATE_CHANGED.value,
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

    def transition_trip_state(self, trip_id: str, new_state: TripStatus) -> TripORM:
        trip = self.get_trip(trip_id)
        old_state = trip.state
        validate_transition(old_state, new_state)
        trip.state = new_state.value if isinstance(new_state, TripStatus) else str(new_state)
        updated_trip = self.repository.update(trip)
        emit_event(
            DomainEvent(
                name=DomainEventName.TRIP_STATE_CHANGED.value,
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

    def start_trip(self, trip_id: str) -> TripORM:
        trip = self.get_trip(trip_id)
        validate_transition(trip.state, TripStatus.BOARDING)
        trip.state = TripStatus.BOARDING.value
        updated_trip = self.repository.update(trip)
        emit_event(
            DomainEvent(
                DomainEventName.TRIP_STARTED.value,
                {
                    "trip_id": updated_trip.id,
                    "driver_id": updated_trip.driver_id,
                    "vehicle_id": updated_trip.vehicle_id,
                    "organization_id": updated_trip.organization_id,
                },
            ),
            session=self.repository.session,
        )
        return updated_trip

    def depart_trip(self, trip_id: str) -> TripORM:
        trip = self.get_trip(trip_id)
        validate_transition(trip.state, TripStatus.ENROUTE)
        trip.state = TripStatus.ENROUTE.value
        updated_trip = self.repository.update(trip)
        emit_event(
            DomainEvent(
                DomainEventName.TRIP_DEPARTED.value,
                {
                    "trip_id": updated_trip.id,
                    "driver_id": updated_trip.driver_id,
                    "vehicle_id": updated_trip.vehicle_id,
                    "organization_id": updated_trip.organization_id,
                },
            ),
            session=self.repository.session,
        )
        return updated_trip

    def create_trip(self, trip_data: TripCreate | dict) -> TripORM:
        payload = trip_data.model_dump() if hasattr(trip_data, "model_dump") else dict(trip_data)
        route = self.route_repository.get_route(payload["route_id"])
        if route is None:
            raise NotFoundError("Route not found")
        variant = self.route_repository.get_variant(payload["route_variant_id"])
        if variant is None or variant.route_id != route.id:
            raise DomainRuleViolationError("Route variant does not belong to the route")

        vehicle = self.vehicle_repository.get_by_id(payload["vehicle_id"])
        if vehicle is None:
            raise NotFoundError("Vehicle not found")
        if vehicle.organization_id != payload["organization_id"] or route.organization_id != payload["organization_id"]:
            raise DomainRuleViolationError("Trip organization must match route and vehicle organization")

        driver = self.driver_repository.get_by_id(payload["driver_id"])
        if driver is None:
            raise NotFoundError("Driver not found")
        if driver.organization_id != payload["organization_id"]:
            raise DomainRuleViolationError("Trip driver must belong to the same organization")

        trip = TripORM(**payload)
        created_trip = self.repository.create(trip)
        emit_event(
            DomainEvent(
                name=DomainEventName.TRIP_CREATED.value,
                payload={
                    "trip_id": created_trip.id,
                    "organization_id": created_trip.organization_id,
                },
            ),
            session=self.repository.session,
        )
        return created_trip
