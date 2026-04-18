from sqlalchemy.orm import Session

from app.application.context import Actor
from app.application.services import (
    AuthApplicationService,
    BookingApplicationService,
    DispatchApplicationService,
    DriverApplicationService,
    OrganizationApplicationService,
    PaymentApplicationService,
    QRApplicationService,
    RankApplicationService,
    RouteApplicationService,
    ShiftApplicationService,
    StopApplicationService,
    SystemApplicationService,
    TripApplicationService,
    UserApplicationService,
    VehicleApplicationService,
)
from app.domain.auth.repository import UserRepository
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.service import BookingService
from app.domain.dispatch.service import DispatchService
from app.domain.drivers.repository import DriverRepository
from app.domain.drivers.service import DriverService
from app.domain.organizations.repository import OrganizationRepository
from app.domain.payments.repository import PaymentRepository
from app.domain.payments.service import PaymentService
from app.domain.qr.repository import QRRepository
from app.domain.qr.service import QRService
from app.domain.ranks.repository import RankQueueRepository
from app.domain.ranks.service import RankService
from app.domain.routes.repository import RouteRepository
from app.domain.routes.service import RouteAdminService
from app.domain.shifts.repository import ShiftRepository
from app.domain.shifts.service import ShiftService
from app.domain.trips.repository import TripRepository
from app.domain.trips.service import TripService
from app.domain.vehicles.repository import VehicleRepository
from app.domain.vehicles.service import VehicleService
from app.integrations.payments.mock_provider import MockPaymentProvider


class ApplicationServices:
    def __init__(self, session: Session, actor: Actor | None = None, request_source: str = "api") -> None:
        self.session = session
        self.actor = actor
        self.request_source = request_source

        self.user_repository = UserRepository(session)
        self.organization_repository = OrganizationRepository(session)
        self.vehicle_repository = VehicleRepository(session)
        self.driver_repository = DriverRepository(session)
        self.shift_repository = ShiftRepository(session)
        self.route_repository = RouteRepository(session)
        self.trip_repository = TripRepository(session)
        self.booking_repository = BookingRepository(session)
        self.payment_repository = PaymentRepository(session)
        self.qr_repository = QRRepository(session)
        self.rank_repository = RankQueueRepository(session)

        self.route_domain_service = RouteAdminService(repository=self.route_repository)
        self.trip_domain_service = TripService(
            repository=self.trip_repository,
            route_repository=self.route_repository,
            driver_repository=self.driver_repository,
            vehicle_repository=self.vehicle_repository,
        )
        self.shift_domain_service = ShiftService(
            repository=self.shift_repository,
            driver_repository=self.driver_repository,
            vehicle_repository=self.vehicle_repository,
        )
        self.dispatch_domain_service = DispatchService(
            route_repository=self.route_repository,
            trip_repository=self.trip_repository,
        )
        self.payment_domain_service = PaymentService(
            repository=self.payment_repository,
            provider=MockPaymentProvider(),
        )
        self.qr_domain_service = QRService(
            qr_repository=self.qr_repository,
            booking_repository=self.booking_repository,
        )
        self.rank_domain_service = RankService(
            repository=self.rank_repository,
            booking_repository=self.booking_repository,
            trip_repository=self.trip_repository,
            route_repository=self.route_repository,
            qr_service=self.qr_domain_service,
            payment_service=self.payment_domain_service,
        )
        self.booking_domain_service = BookingService(
            trip_repository=self.trip_repository,
            route_repository=self.route_repository,
            booking_repository=self.booking_repository,
            payment_service=self.payment_domain_service,
            qr_service=self.qr_domain_service,
            dispatch_service=self.dispatch_domain_service,
        )

        self.auth = AuthApplicationService(
            session,
            actor,
            request_source=request_source,
            user_repository=self.user_repository,
        )
        self.users = UserApplicationService(
            session,
            actor,
            request_source=request_source,
            repository=self.user_repository,
        )
        self.organizations = OrganizationApplicationService(
            session,
            actor,
            request_source=request_source,
            repository=self.organization_repository,
        )
        self.vehicles = VehicleApplicationService(
            session,
            actor,
            request_source=request_source,
            repository=self.vehicle_repository,
        )
        self.drivers = DriverApplicationService(
            session,
            actor,
            request_source=request_source,
            repository=self.driver_repository,
        )
        self.stops = StopApplicationService(
            session,
            actor,
            request_source=request_source,
            service=self.route_domain_service,
        )
        self.routes = RouteApplicationService(
            session,
            actor,
            request_source=request_source,
            service=self.route_domain_service,
        )
        self.shifts = ShiftApplicationService(
            session,
            actor,
            request_source=request_source,
            service=self.shift_domain_service,
            driver_repository=self.driver_repository,
        )
        self.trips = TripApplicationService(
            session,
            actor,
            request_source=request_source,
            service=self.trip_domain_service,
        )
        self.dispatch = DispatchApplicationService(
            session,
            actor,
            request_source=request_source,
            service=self.dispatch_domain_service,
        )
        self.bookings = BookingApplicationService(
            session,
            actor,
            request_source=request_source,
            service=self.booking_domain_service,
        )
        self.payments = PaymentApplicationService(
            session,
            actor,
            request_source=request_source,
            service=self.payment_domain_service,
        )
        self.qr = QRApplicationService(
            session,
            actor,
            request_source=request_source,
            service=self.qr_domain_service,
        )
        self.ranks = RankApplicationService(
            session,
            actor,
            request_source=request_source,
            service=self.rank_domain_service,
        )
        self.system = SystemApplicationService(session, actor, request_source=request_source)


def build_application_services(
    session: Session,
    actor: Actor | None = None,
    request_source: str = "api",
) -> ApplicationServices:
    return ApplicationServices(session=session, actor=actor, request_source=request_source)
