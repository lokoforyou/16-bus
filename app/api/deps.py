from collections.abc import Generator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import clear_database_caches, get_db
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.domain.auth.models import UserORM
from app.domain.auth.repository import UserRepository
from app.domain.auth.schemas import TokenData
from app.domain.auth.service import AuthService
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.service import BookingService
from app.domain.dispatch.service import DispatchService
from app.domain.drivers.repository import DriverRepository
from app.domain.drivers.service import DriverService
from app.domain.organizations.repository import OrganizationRepository
from app.domain.organizations.service import OrganizationService
from app.domain.payments.repository import PaymentRepository
from app.domain.payments.service import PaymentService
from app.integrations.payments.mock_provider import MockPaymentProvider
from app.domain.qr.repository import QRRepository
from app.domain.qr.service import QRService
from app.domain.routes.repository import RouteRepository
from app.domain.routes.service import RouteAdminService
from app.domain.shifts.repository import ShiftRepository
from app.domain.shifts.service import ShiftService
from app.domain.trips.repository import TripRepository
from app.domain.trips.service import TripService
from app.domain.vehicles.repository import VehicleRepository
from app.domain.vehicles.service import VehicleService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_request_context() -> dict[str, str]:
    return {"request_source": "api"}


def get_db_session() -> Generator:
    yield from get_db()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(session=db)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repository=user_repository)


def get_organization_repository(db: Session = Depends(get_db)) -> OrganizationRepository:
    return OrganizationRepository(session=db)


def get_organization_service(
    organization_repository: OrganizationRepository = Depends(get_organization_repository),
) -> OrganizationService:
    return OrganizationService(repository=organization_repository)


def get_vehicle_repository(db: Session = Depends(get_db)) -> VehicleRepository:
    return VehicleRepository(session=db)


def get_vehicle_service(
    vehicle_repository: VehicleRepository = Depends(get_vehicle_repository),
) -> VehicleService:
    return VehicleService(repository=vehicle_repository)


def get_driver_repository(db: Session = Depends(get_db)) -> DriverRepository:
    return DriverRepository(session=db)


def get_driver_service(
    driver_repository: DriverRepository = Depends(get_driver_repository),
) -> DriverService:
    return DriverService(repository=driver_repository)


def get_shift_repository(db: Session = Depends(get_db)) -> ShiftRepository:
    return ShiftRepository(session=db)


def get_shift_service(
    shift_repository: ShiftRepository = Depends(get_shift_repository),
    driver_repository: DriverRepository = Depends(get_driver_repository),
    vehicle_repository: VehicleRepository = Depends(get_vehicle_repository),
) -> ShiftService:
    return ShiftService(
        repository=shift_repository,
        driver_repository=driver_repository,
        vehicle_repository=vehicle_repository
    )


async def get_current_user_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        org_id: str = payload.get("org_id")
        if user_id is None:
            raise AuthenticationError("Could not validate credentials")
        return TokenData(user_id=user_id, role=role, organization_id=org_id)
    except JWTError:
        raise AuthenticationError("Could not validate credentials")


async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserORM:
    return auth_service.get_user_by_id(token_data.user_id)


def get_route_repository(db: Session = Depends(get_db)) -> RouteRepository:
    return RouteRepository(session=db)


def get_route_service(
    route_repository: RouteRepository = Depends(get_route_repository),
) -> RouteAdminService:
    return RouteAdminService(repository=route_repository)


def get_trip_repository(db: Session = Depends(get_db)) -> TripRepository:
    return TripRepository(session=db)


def get_trip_service(
    trip_repository: TripRepository = Depends(get_trip_repository),
    route_repository: RouteRepository = Depends(get_route_repository),
    driver_repository: DriverRepository = Depends(get_driver_repository),
    vehicle_repository: VehicleRepository = Depends(get_vehicle_repository),
    shift_repository: ShiftRepository = Depends(get_shift_repository),
) -> TripService:
    return TripService(
        repository=trip_repository,
        route_repository=route_repository,
        driver_repository=driver_repository,
        vehicle_repository=vehicle_repository,
        shift_repository=shift_repository,
    )


def get_qr_repository(db: Session = Depends(get_db)) -> QRRepository:
    return QRRepository(session=db)


def get_booking_repository(
    db: Session = Depends(get_db),
) -> BookingRepository:
    return BookingRepository(session=db)


def get_payment_repository(db: Session = Depends(get_db)) -> PaymentRepository:
    return PaymentRepository(session=db)


def get_payment_service(
    repository: PaymentRepository = Depends(get_payment_repository),
) -> PaymentService:
    return PaymentService(repository=repository, provider=MockPaymentProvider())


def get_qr_service(
    qr_repository: QRRepository = Depends(get_qr_repository),
    booking_repository: BookingRepository = Depends(get_booking_repository),
) -> QRService:
    return QRService(
        qr_repository=qr_repository,
        booking_repository=booking_repository,
    )


def get_booking_service(
    trip_repository: TripRepository = Depends(get_trip_repository),
    route_repository: RouteRepository = Depends(get_route_repository),
    booking_repository: BookingRepository = Depends(get_booking_repository),
    payment_service: PaymentService = Depends(get_payment_service),
    qr_service: QRService = Depends(get_qr_service),
    dispatch_service: DispatchService = Depends(get_dispatch_service),
) -> BookingService:
    return BookingService(
        trip_repository=trip_repository,
        route_repository=route_repository,
        booking_repository=booking_repository,
        payment_service=payment_service,
        qr_service=qr_service,
        dispatch_service=dispatch_service,
    )


def reset_dependency_state() -> None:
    clear_database_caches()
