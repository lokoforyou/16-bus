from app.application.base import ApplicationService
from app.application.context import require_authenticated, require_org_access, require_roles
from app.core.bootstrap import seed_reference_data
from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.domain.auth.models import UserORM, UserRole
from app.domain.auth.repository import UserRepository
from app.domain.auth.schemas import LoginRequest, Token, User, UserCreate, UserUpdate
from app.domain.auth.service import AuthService
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.schemas import (
    BookingCancelResponse,
    BookingCreatedResponse,
    BookingDetailResponse,
    BookingPaymentResponse,
    BookingRead,
    BookingQuoteRequest,
    BookingQuoteResponse,
    CreateBookingAdminRequest,
    CreateBookingRequest,
)
from app.domain.bookings.service import BookingService
from app.domain.dispatch.service import DispatchService
from app.domain.drivers.models import DriverORM
from app.domain.drivers.repository import DriverRepository
from app.domain.drivers.schemas import DriverCreate, DriverUpdate
from app.domain.drivers.service import DriverService
from app.domain.organizations.models import OrganizationORM
from app.domain.organizations.repository import OrganizationRepository
from app.domain.organizations.schemas import OrganizationCreate, OrganizationUpdate
from app.domain.organizations.service import OrganizationService
from app.domain.payments.repository import PaymentRepository
from app.domain.payments.schemas import PaymentDetailResponse, PaymentRequest
from app.domain.payments.service import PaymentService
from app.domain.qr.repository import QRRepository
from app.domain.qr.schemas import BoardingScanRequest, BoardingScanResponse
from app.domain.qr.service import QRService
from app.domain.ranks.repository import RankQueueRepository
from app.domain.ranks.schemas import RankCashAuthorizationRequest, RankQueueTicketRead, RankTicketAssignRequest, RankTicketIssueRequest
from app.domain.ranks.service import RankService
from app.domain.routes.models import StopORM
from app.domain.routes.repository import RouteRepository
from app.domain.routes.schemas import (
    RouteCreate,
    RouteListResponse,
    RouteStopCreate,
    RouteStopListResponse,
    StopCreate,
    StopListResponse,
    StopRead,
    StopUpdate,
)
from app.domain.routes.service import RouteAdminService
from app.domain.shifts.models import DriverShiftORM
from app.domain.shifts.repository import ShiftRepository
from app.domain.shifts.schemas import ShiftCreate
from app.domain.shifts.service import ShiftService
from app.domain.trips.models import TripORM, TripStatus
from app.domain.trips.repository import TripRepository
from app.domain.trips.schemas import TripCreate, TripUpdate
from app.domain.trips.service import TripService
from app.domain.vehicles.models import VehicleORM
from app.domain.vehicles.repository import VehicleRepository
from app.domain.vehicles.schemas import VehicleCreate, VehicleUpdate
from app.domain.vehicles.service import VehicleService
from app.integrations.payments.mock_provider import MockPaymentProvider
from typing import List


class AuthApplicationService(ApplicationService):
    def __init__(self, *args, user_repository: UserRepository, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user_repository = user_repository
        self.service = AuthService(repository=user_repository)

    def login(self, request: LoginRequest) -> Token:
        return self.service.authenticate(request)

    def get_current_user(self) -> UserORM:
        actor = require_authenticated(self.actor)
        return self.service.get_user_by_id(actor.user_id)

    def register(self, data: UserCreate) -> UserORM:
        return self.transact(lambda: self.service.register(data))


class UserApplicationService(ApplicationService):
    def __init__(self, *args, repository: UserRepository, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.repository = repository
        self.service = AuthService(repository=repository)

    def list_users(self, organization_id: str | None = None) -> List[UserORM]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        if organization_id:
            require_org_access(self.actor, organization_id)
        elif self.actor and self.actor.role != UserRole.SUPER_ADMIN:
            organization_id = self.actor.organization_id
        return self.repository.list(organization_id=organization_id)

    def create_user(self, data: UserCreate) -> UserORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        return self.transact(lambda: self.service.register(data))

    def get_user(self, user_id: str) -> UserORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if user.organization_id:
            require_org_access(self.actor, user.organization_id)
        return user

    def update_user(self, user_id: str, data: UserUpdate) -> UserORM:
        user = self.get_user(user_id)

        def operation() -> UserORM:
            payload = data.model_dump(exclude_unset=True)
            if "organization_id" in payload and payload["organization_id"] is not None:
                require_org_access(self.actor, payload["organization_id"])
            if "password" in payload and payload["password"]:
                user.password_hash = hash_password(payload.pop("password"))
            for field, value in payload.items():
                setattr(user, field, value)
            return self.repository.update(user)

        return self.transact(operation)

    def delete_user(self, user_id: str) -> dict[str, str]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        user = self.get_user(user_id)
        self.transact(lambda: self.repository.delete(user))
        return {"status": "deleted", "user_id": user_id}


class OrganizationApplicationService(ApplicationService):
    def __init__(self, *args, repository: OrganizationRepository, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = OrganizationService(repository=repository)

    def create(self, data: OrganizationCreate) -> OrganizationORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        return self.transact(lambda: self.service.create_organization(data))

    def list(self) -> List[OrganizationORM]:
        return self.service.list_organizations()

    def get(self, organization_id: str) -> OrganizationORM:
        organization = self.service.get_organization(organization_id)
        if self.actor and self.actor.role != UserRole.SUPER_ADMIN:
            require_org_access(self.actor, organization.id)
        return organization

    def update(self, organization_id: str, data: OrganizationUpdate) -> OrganizationORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        require_org_access(self.actor, organization_id)
        return self.transact(lambda: self.service.update_organization(organization_id, data))

    def delete(self, organization_id: str) -> dict[str, str]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        self.transact(lambda: self.service.delete_organization(organization_id))
        return {"status": "deleted", "organization_id": organization_id}


class VehicleApplicationService(ApplicationService):
    def __init__(self, *args, repository: VehicleRepository, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = VehicleService(repository=repository)

    def create(self, data: VehicleCreate) -> VehicleORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        require_org_access(self.actor, data.organization_id)
        return self.transact(lambda: self.service.create_vehicle(data))

    def list(self, organization_id: str | None = None) -> List[VehicleORM]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.DRIVER])
        if organization_id:
            require_org_access(self.actor, organization_id)
        elif self.actor and self.actor.role != UserRole.SUPER_ADMIN:
            organization_id = self.actor.organization_id
        return self.service.list_vehicles(organization_id)

    def get(self, vehicle_id: str) -> VehicleORM:
        vehicle = self.service.get_vehicle(vehicle_id)
        require_org_access(self.actor, vehicle.organization_id)
        return vehicle

    def update(self, vehicle_id: str, data: VehicleUpdate) -> VehicleORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        vehicle = self.service.get_vehicle(vehicle_id)
        require_org_access(self.actor, vehicle.organization_id)
        if data.organization_id:
            require_org_access(self.actor, data.organization_id)
        return self.transact(lambda: self.service.update_vehicle(vehicle_id, data))


class DriverApplicationService(ApplicationService):
    def __init__(self, *args, repository: DriverRepository, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = DriverService(repository=repository)

    def create(self, data: DriverCreate) -> DriverORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        require_org_access(self.actor, data.organization_id)
        return self.transact(lambda: self.service.create_driver(data))

    def list(self, organization_id: str | None = None) -> List[DriverORM]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.DRIVER])
        if organization_id:
            require_org_access(self.actor, organization_id)
        elif self.actor and self.actor.role != UserRole.SUPER_ADMIN:
            organization_id = self.actor.organization_id
        return self.service.list_drivers(organization_id)

    def get(self, driver_id: str) -> DriverORM:
        driver = self.service.get_driver(driver_id)
        require_org_access(self.actor, driver.organization_id)
        return driver

    def update(self, driver_id: str, data: DriverUpdate) -> DriverORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        driver = self.service.get_driver(driver_id)
        require_org_access(self.actor, driver.organization_id)
        if data.organization_id:
            require_org_access(self.actor, data.organization_id)
        return self.transact(lambda: self.service.update_driver(driver_id, data))

    def delete(self, driver_id: str) -> dict[str, str]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        driver = self.service.get_driver(driver_id)
        require_org_access(self.actor, driver.organization_id)
        self.transact(lambda: self.service.delete_driver(driver_id))
        return {"status": "deleted", "driver_id": driver_id}


class StopApplicationService(ApplicationService):
    def __init__(self, *args, service: RouteAdminService, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = service

    def list(self, active_only: bool = False) -> StopListResponse:
        return StopListResponse(**self.service.list_stops(active_only=active_only))

    def get(self, stop_id: str) -> StopORM:
        return self.service.get_stop(stop_id)

    def create(self, data: StopCreate) -> StopORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        return self.transact(lambda: self.service.create_stop(data))

    def update(self, stop_id: str, data: StopUpdate) -> StopORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        return self.transact(lambda: self.service.update_stop(stop_id, data))

    def delete(self, stop_id: str) -> dict[str, str]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        self.transact(lambda: self.service.delete_stop(stop_id))
        return {"status": "deleted", "stop_id": stop_id}


class RouteApplicationService(ApplicationService):
    def __init__(self, *args, service: RouteAdminService, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = service

    def list(self) -> RouteListResponse:
        return RouteListResponse(**self.service.list_routes())

    def get(self, route_id: str):
        route = self.service.get_route(route_id)
        if self.actor and self.actor.role != UserRole.SUPER_ADMIN:
            require_org_access(self.actor, route.organization_id)
        return route

    def list_route_stops(self, route_id: str) -> RouteStopListResponse:
        route = self.service.get_route(route_id)
        if self.actor and self.actor.role != UserRole.SUPER_ADMIN:
            require_org_access(self.actor, route.organization_id)
        return RouteStopListResponse(**self.service.list_route_stops(route_id))

    def create(self, data: RouteCreate):
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        require_org_access(self.actor, data.organization_id)
        return self.transact(lambda: self.service.create_route(data))

    def create_variant(self, route_id: str, data):
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        route = self.service.get_route(route_id)
        require_org_access(self.actor, route.organization_id)
        return self.transact(lambda: self.service.create_variant(route_id, data))

    def add_stop_to_variant(self, route_id: str, variant_id: str, data: RouteStopCreate):
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        route = self.service.get_route(route_id)
        require_org_access(self.actor, route.organization_id)
        return self.transact(lambda: self.service.add_stop_to_variant(route_id, variant_id, data))


class ShiftApplicationService(ApplicationService):
    def __init__(
        self,
        *args,
        service: ShiftService,
        driver_repository: DriverRepository,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.service = service
        self.driver_repository = driver_repository

    def start(self, data: ShiftCreate) -> DriverShiftORM:
        require_roles(self.actor, [UserRole.DRIVER])
        return self.transact(lambda: self.service.start_shift(data, actor_user_id=self.actor.user_id if self.actor else None))

    def end(self, shift_id: str) -> DriverShiftORM:
        require_roles(self.actor, [UserRole.DRIVER])
        return self.transact(lambda: self.service.end_shift(shift_id, actor_user_id=self.actor.user_id if self.actor else None))

    def current(self) -> DriverShiftORM:
        require_roles(self.actor, [UserRole.DRIVER])
        return self.service.get_active_shift_for_driver(self.actor.user_id if self.actor else "")

    def list(self, organization_id: str | None = None) -> List[DriverShiftORM]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        if organization_id is None and self.actor and self.actor.role != UserRole.SUPER_ADMIN:
            organization_id = self.actor.organization_id
        if organization_id is None:
            raise NotFoundError("Organization id is required")
        require_org_access(self.actor, organization_id)
        return self.service.list_organization_shifts(organization_id)


class TripApplicationService(ApplicationService):
    def __init__(self, *args, service: TripService, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = service

    def list(self, organization_id: str | None = None) -> List[TripORM]:
        if self.actor:
            require_authenticated(self.actor)
            if organization_id:
                require_org_access(self.actor, organization_id)
            elif self.actor.role != UserRole.SUPER_ADMIN:
                organization_id = self.actor.organization_id
        return self.service.list_trips(organization_id=organization_id)

    def list_all(self) -> List[TripORM]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        return self.service.list_trips()

    def list_active(self, organization_id: str | None = None, route_id: str | None = None) -> List[TripORM]:
        trips = self.list(organization_id=organization_id)
        if route_id:
            trips = [trip for trip in trips if trip.route_id == route_id]
        return [trip for trip in trips if trip.state in {"planned", "boarding", "enroute"}]

    def get(self, trip_id: str) -> TripORM:
        trip = self.service.get_trip(trip_id)
        if self.actor and self.actor.role != UserRole.SUPER_ADMIN:
            require_org_access(self.actor, trip.organization_id)
        return trip

    def create(self, request: TripCreate) -> TripORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        require_org_access(self.actor, request.organization_id)
        return self.transact(lambda: self.service.create_trip(request))

    def update(self, trip_id: str, data: TripUpdate) -> TripORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
        trip = self.service.get_trip(trip_id)
        require_org_access(self.actor, trip.organization_id)
        if getattr(data, "organization_id", None):
            require_org_access(self.actor, data.organization_id)
        return self.transact(lambda: self.service.update_trip(trip_id, data))

    def transition(self, trip_id: str, new_state: TripStatus) -> TripORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.DRIVER])
        trip = self.service.get_trip(trip_id)
        require_org_access(self.actor, trip.organization_id)
        return self.transact(lambda: self.service.transition_trip_state(trip_id, new_state))

    def accept(self, trip_id: str) -> TripORM:
        return self.transition(trip_id, TripStatus.BOARDING)

    def start(self, trip_id: str) -> TripORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.DRIVER, UserRole.MARSHAL])
        trip = self.service.get_trip(trip_id)
        require_org_access(self.actor, trip.organization_id)
        return self.transact(lambda: self.service.start_trip(trip_id))

    def depart(self, trip_id: str) -> TripORM:
        require_roles(self.actor, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.DRIVER, UserRole.MARSHAL])
        trip = self.service.get_trip(trip_id)
        require_org_access(self.actor, trip.organization_id)
        return self.transact(lambda: self.service.depart_trip(trip_id))


class DispatchApplicationService(ApplicationService):
    def __init__(self, *args, service: DispatchService, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = service

    def quote(self, request: BookingQuoteRequest) -> BookingQuoteResponse:
        candidates = self.service.find_trip_candidates(
            route_id=request.route_id,
            origin_stop_id=request.origin_stop_id,
            destination_stop_id=request.destination_stop_id,
            party_size=request.party_size,
        )
        return BookingQuoteResponse(candidates=candidates)


class BookingApplicationService(ApplicationService):
    def __init__(self, *args, service: BookingService, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = service

    def quote(self, request: BookingQuoteRequest) -> BookingQuoteResponse:
        return self.service.quote(request)

    def create(self, request: CreateBookingRequest) -> BookingCreatedResponse:
        actor = require_roles(self.actor, [UserRole.PASSENGER])
        return self.transact(lambda: self.service.create_booking(request, actor.user_id or ""))

    def create_admin(self, request: CreateBookingAdminRequest) -> BookingCreatedResponse:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        return self.transact(lambda: self.service.create_booking_admin(request))

    def get(self, booking_id: str) -> BookingDetailResponse:
        actor = require_roles(self.actor, [UserRole.PASSENGER])
        return self.service.get_booking(booking_id, actor.user_id or "")

    def list_all(self) -> List[BookingRead]:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        return [BookingRead.model_validate(booking) for booking in self.service.booking_repository.all()]

    def get_admin(self, booking_id: str) -> BookingDetailResponse:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        booking = self.service.booking_repository.get(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        return BookingDetailResponse(booking=booking)

    def pay(self, booking_id: str, request: PaymentRequest) -> BookingPaymentResponse:
        actor = require_roles(self.actor, [UserRole.PASSENGER])
        return self.transact(lambda: self.service.pay_booking(booking_id, request, actor.user_id or ""))

    def cancel(self, booking_id: str) -> BookingCancelResponse:
        actor = require_roles(self.actor, [UserRole.PASSENGER])
        return self.transact(lambda: self.service.cancel_booking(booking_id, actor.user_id or ""))

    def cancel_admin(self, booking_id: str) -> BookingCancelResponse:
        require_roles(self.actor, [UserRole.SUPER_ADMIN])
        return self.transact(lambda: self.service.cancel_booking_as_operator(booking_id))


class PaymentApplicationService(ApplicationService):
    def __init__(self, *args, service: PaymentService, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = service

    def get(self, payment_id: str) -> PaymentDetailResponse:
        require_authenticated(self.actor)
        payment = self.service.get_payment(payment_id)
        if payment is None:
            raise NotFoundError("Payment not found")
        return payment


class QRApplicationService(ApplicationService):
    def __init__(self, *args, service: QRService, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = service

    def scan(self, request: BoardingScanRequest) -> BoardingScanResponse:
        require_roles(self.actor, [UserRole.DRIVER, UserRole.MARSHAL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN])
        return self.transact(lambda: self.service.validate_and_scan(request))


class RankApplicationService(ApplicationService):
    def __init__(self, *args, service: RankService, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.service = service

    def issue_ticket(self, request: RankTicketIssueRequest) -> RankQueueTicketRead:
        require_roles(self.actor, [UserRole.MARSHAL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN])
        return self.transact(lambda: self.service.issue_ticket(request))

    def assign_ticket(self, request: RankTicketAssignRequest) -> RankQueueTicketRead:
        require_roles(self.actor, [UserRole.MARSHAL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN])
        return self.transact(lambda: self.service.assign_ticket(request))

    def board_ticket(self, ticket_id: str) -> RankQueueTicketRead:
        require_roles(self.actor, [UserRole.MARSHAL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN])
        return self.transact(lambda: self.service.board_ticket(ticket_id))

    def authorize_cash_booking(self, request: RankCashAuthorizationRequest) -> dict[str, object]:
        require_roles(self.actor, [UserRole.MARSHAL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN])
        return self.transact(lambda: self.service.authorize_cash_booking(request))

    def open_trip(self, trip_id: str) -> dict[str, str]:
        require_roles(self.actor, [UserRole.MARSHAL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN, UserRole.DRIVER])
        return self.transact(lambda: self.service.open_trip(trip_id))

    def depart_trip(self, trip_id: str) -> dict[str, str]:
        require_roles(self.actor, [UserRole.MARSHAL, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN, UserRole.DRIVER])
        return self.transact(lambda: self.service.depart_trip(trip_id))


class SystemApplicationService(ApplicationService):
    def seed(self) -> dict[str, str]:
        self.transact(lambda: seed_reference_data(self.session))
        return {"status": "seeded"}

    def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def recent_events(self, limit: int = 20) -> List[dict[str, object]]:
        from sqlalchemy import select

        from app.core.events import DomainEventRecordORM

        stmt = select(DomainEventRecordORM).order_by(DomainEventRecordORM.emitted_at.desc()).limit(limit)
        events = list(self.session.scalars(stmt).all())
        return [
            {
                "id": event.id,
                "name": event.name,
                "payload": event.payload,
                "emitted_at": event.emitted_at,
            }
            for event in events
        ]
