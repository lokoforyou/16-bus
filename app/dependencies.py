from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import clear_database_caches, get_db
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.service import BookingService
from app.domain.dispatch.service import DispatchService
from app.domain.payments.repository import PaymentRepository
from app.domain.payments.service import PaymentService
from app.domain.qr.repository import QRRepository
from app.domain.qr.service import QRService
from app.domain.routes.repository import RouteRepository
from app.domain.routes.service import RouteService
from app.domain.trips.repository import TripRepository
from app.domain.trips.service import TripService


def get_route_repository(db: Session = Depends(get_db)) -> RouteRepository:
    return RouteRepository(session=db)


def get_trip_repository(db: Session = Depends(get_db)) -> TripRepository:
    return TripRepository(session=db)


def get_booking_repository(
    db: Session = Depends(get_db),
    trip_repository: TripRepository = Depends(get_trip_repository),
) -> BookingRepository:
    return BookingRepository(session=db, trip_repository=trip_repository)


def get_dispatch_service(
    route_repository: RouteRepository = Depends(get_route_repository),
    trip_repository: TripRepository = Depends(get_trip_repository),
) -> DispatchService:
    return DispatchService(
        route_repository=route_repository,
        trip_repository=trip_repository,
    )


def get_payment_repository(db: Session = Depends(get_db)) -> PaymentRepository:
    return PaymentRepository(session=db)


def get_qr_repository(db: Session = Depends(get_db)) -> QRRepository:
    return QRRepository(session=db)


def get_route_service(
    route_repository: RouteRepository = Depends(get_route_repository),
) -> RouteService:
    return RouteService(repository=route_repository)


def get_trip_service(
    trip_repository: TripRepository = Depends(get_trip_repository),
) -> TripService:
    return TripService(repository=trip_repository)


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
    booking_repository: BookingRepository = Depends(get_booking_repository),
    payment_repository: PaymentRepository = Depends(get_payment_repository),
    qr_service: QRService = Depends(get_qr_service),
    dispatch_service: DispatchService = Depends(get_dispatch_service),
) -> BookingService:
    return BookingService(
        trip_repository=trip_repository,
        booking_repository=booking_repository,
        payment_repository=payment_repository,
        qr_service=qr_service,
        dispatch_service=dispatch_service,
    )


def get_payment_service(
    payment_repository: PaymentRepository = Depends(get_payment_repository),
) -> PaymentService:
    return PaymentService(repository=payment_repository)


def reset_dependency_state() -> None:
    clear_database_caches()
