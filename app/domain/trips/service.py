from app.core.exceptions import DomainRuleViolationError, NotFoundError
from app.domain.drivers.repository import DriverRepository
from app.domain.routes.repository import RouteRepository
from app.domain.shifts.repository import ShiftRepository
from app.domain.shifts.models import ShiftStatus
from app.domain.trips.models import TripORM, TripStatus
from app.domain.trips.repository import TripRepository
from app.domain.trips.schemas import TripCreate
from app.domain.trips.state_machine import validate_transition
from app.domain.vehicles.repository import VehicleRepository


class TripService:
    def __init__(
        self,
        repository: TripRepository,
        route_repository: RouteRepository,
        driver_repository: DriverRepository,
        vehicle_repository: VehicleRepository,
        shift_repository: ShiftRepository,
    ):
        self.repository = repository
        self.route_repository = route_repository
        self.driver_repository = driver_repository
        self.vehicle_repository = vehicle_repository
        self.shift_repository = shift_repository

    def get_trip(self, trip_id: str) -> TripORM:
        trip = self.repository.get_trip(trip_id)
        if not trip:
            raise NotFoundError("Trip not found")
        return trip

    def transition_trip_state(self, trip_id: str, new_state: TripStatus) -> TripORM:
        with self.repository.session.begin():
            trip = self.get_trip(trip_id)
            validate_transition(trip.state, new_state)
            trip.state = new_state.value
            return self.repository.update(trip)

    def create_trip(self, data: TripCreate) -> TripORM:
        with self.repository.session.begin():
            route = self.route_repository.get_route(data.route_id)
            if route is None:
                raise NotFoundError("Route not found")

            variant = self.route_repository.get_variant(data.route_variant_id)
            if variant is None or variant.route_id != data.route_id:
                raise DomainRuleViolationError("Route variant does not belong to route")

            driver = self.driver_repository.get_by_id(data.driver_id)
            if driver is None or not driver.is_active:
                raise DomainRuleViolationError("Driver is invalid or inactive")

            vehicle = self.vehicle_repository.get_by_id(data.vehicle_id)
            if vehicle is None or not vehicle.is_active:
                raise DomainRuleViolationError("Vehicle is invalid or inactive")

            if route.organization_id != data.organization_id:
                raise DomainRuleViolationError("Trip organization must match route organization")
            if driver.organization_id != data.organization_id:
                raise DomainRuleViolationError("Trip organization must match driver organization")
            if vehicle.organization_id != data.organization_id:
                raise DomainRuleViolationError("Trip organization must match vehicle organization")

            shift = self.shift_repository.get_active_by_driver(data.driver_id)
            if shift is None or shift.status != ShiftStatus.ACTIVE or shift.vehicle_id != data.vehicle_id:
                raise DomainRuleViolationError("Driver must have an active shift with the selected vehicle")

            current_stop_sequence = self.route_repository.get_stop_sequence(data.route_variant_id, data.current_stop_id)
            if current_stop_sequence is None:
                raise DomainRuleViolationError("Current stop must belong to route variant")

            if data.seats_free > data.seats_total:
                raise DomainRuleViolationError("seats_free cannot exceed seats_total")

            state = TripStatus(data.state)
            if state not in {TripStatus.PLANNED, TripStatus.BOARDING}:
                raise DomainRuleViolationError("Initial trip state must be planned or boarding")

            trip = TripORM(**data.model_dump())
            return self.repository.create(trip)
