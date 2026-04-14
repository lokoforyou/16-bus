from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.config import get_settings
from app.core.exceptions import ConflictError, DomainRuleViolationError, NotFoundError, PermissionDeniedError
from app.core.events import DomainEvent, emit_event
from app.domain.bookings.models import BookingORM, BookingStatus
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.schemas import (
    BookingCancelResponse,
    BookingCreatedResponse,
    BookingDetailResponse,
    BookingQuoteRequest,
    BookingQuoteResponse,
    CreateBookingRequest,
)
from app.domain.bookings.state_machine import validate_transition
from app.domain.payments.schemas import PaymentRequest
from app.domain.payments.service import PaymentService
from app.domain.qr.service import QRService
from app.domain.routes.repository import RouteRepository
from app.domain.trips.models import TripStatus
from app.domain.trips.repository import TripRepository
from app.domain.trips.schemas import TripRead


class BookingService:
    def __init__(
        self,
        trip_repository: TripRepository,
        route_repository: RouteRepository,
        booking_repository: BookingRepository,
        payment_service: PaymentService,
        qr_service: QRService,
    ) -> None:
        self.trip_repository = trip_repository
        self.route_repository = route_repository
        self.booking_repository = booking_repository
        self.payment_service = payment_service
        self.qr_service = qr_service

    def quote(self, request: BookingQuoteRequest) -> BookingQuoteResponse:
        trips = self.trip_repository.list_trips()
        candidates = []
        for trip in trips:
            if trip.route_id != request.route_id:
                continue
            if trip.state not in {TripStatus.PLANNED.value, TripStatus.BOARDING.value}:
                continue
            if trip.seats_free < request.party_size:
                continue
            origin_seq = self.route_repository.get_stop_sequence(trip.route_variant_id, request.origin_stop_id)
            destination_seq = self.route_repository.get_stop_sequence(trip.route_variant_id, request.destination_stop_id)
            if origin_seq is None or destination_seq is None or origin_seq >= destination_seq:
                continue
            candidates.append(
                {
                    "trip": TripRead.model_validate(trip),
                    "eta_minutes": 5,
                    "estimated_fare": float(request.party_size * 12.5),
                }
            )
        return BookingQuoteResponse(candidates=candidates)

    def create_booking(self, request: CreateBookingRequest, passenger_id: str) -> BookingCreatedResponse:
        with self.booking_repository.session.begin():
            quote = self.quote(
                BookingQuoteRequest(
                    route_id=request.route_id,
                    origin_stop_id=request.origin_stop_id,
                    destination_stop_id=request.destination_stop_id,
                    party_size=request.party_size,
                )
            )
            if not quote.candidates:
                raise DomainRuleViolationError("No eligible trips for booking request")

            selected_trip_id = quote.candidates[0].trip.id
            trip = self.trip_repository.get_trip_for_update(selected_trip_id)
            if trip is None:
                raise NotFoundError("Trip not found")
            if trip.seats_free < request.party_size:
                raise ConflictError("Not enough seats available")

            self.trip_repository.reserve_seats(trip, request.party_size)

            booking = BookingORM(
                id=f"booking-{uuid4().hex[:12]}",
                trip_id=trip.id,
                passenger_id=passenger_id,
                origin_stop_id=request.origin_stop_id,
                destination_stop_id=request.destination_stop_id,
                party_size=request.party_size,
                fare_amount=float(request.party_size * 12.5),
                hold_expires_at=datetime.now(UTC) + timedelta(minutes=get_settings().booking_hold_minutes),
                payment_status="pending",
                booking_state=BookingStatus.HELD.value,
                forfeiture_fee_amount=0.0,
                booking_channel=request.booking_channel,
                qr_token_id=None,
            )
            booking = self.booking_repository.save(booking)
            emit_event(
                DomainEvent("booking.held", {"booking_id": booking.id, "trip_id": booking.trip_id}),
                session=self.booking_repository.session,
            )
            return BookingCreatedResponse(booking=booking)

    def get_booking(self, booking_id: str, passenger_id: str) -> BookingDetailResponse:
        with self.booking_repository.session.begin():
            booking = self.booking_repository.get(booking_id)
            if booking is None:
                raise NotFoundError("Booking not found")
            self._assert_owner(booking, passenger_id)
            return BookingDetailResponse(booking=booking)

    def pay_booking(self, booking_id: str, request: PaymentRequest, passenger_id: str):
        with self.booking_repository.session.begin():
            booking = self.booking_repository.get_for_update(booking_id)
            if booking is None:
                raise NotFoundError("Booking not found")
            self._assert_owner(booking, passenger_id)

            validate_transition(booking.booking_state, BookingStatus.CONFIRMED)
            payment = self.payment_service.process_payment(
                amount=booking.fare_amount,
                method=request.method,
                booking_id=booking.id,
            )
            booking.booking_state = BookingStatus.CONFIRMED.value
            booking.payment_status = payment.status
            token = self.qr_service.issue_for_booking(booking.id)
            booking.qr_token_id = token.id
            booking = self.booking_repository.update(booking)
            emit_event(
                DomainEvent("booking.confirmed", {"booking_id": booking.id, "payment_id": payment.id}),
                session=self.booking_repository.session,
            )
            return {"booking": booking, "payment_id": payment.id}

    def cancel_booking(self, booking_id: str, passenger_id: str) -> BookingCancelResponse:
        with self.booking_repository.session.begin():
            booking = self.booking_repository.get_for_update(booking_id)
            if booking is None:
                raise NotFoundError("Booking not found")
            self._assert_owner(booking, passenger_id)

            validate_transition(booking.booking_state, BookingStatus.CANCELLED)
            trip = self.trip_repository.get_trip_for_update(booking.trip_id)
            if trip is None:
                raise NotFoundError("Trip not found")
            self.trip_repository.release_seats(trip, booking.party_size)

            booking.booking_state = BookingStatus.CANCELLED.value
            if booking.payment_status == "captured":
                self.payment_service.refund_payment(booking.id)
                booking.payment_status = "refunded"

            self.qr_service.void_for_booking(booking.id)
            booking = self.booking_repository.update(booking)
            emit_event(
                DomainEvent("booking.cancelled", {"booking_id": booking.id, "trip_id": booking.trip_id}),
                session=self.booking_repository.session,
            )
            return BookingCancelResponse(booking=booking)

    def expire_stale_holds(self) -> int:
        with self.booking_repository.session.begin():
            expired = 0
            for booking in self.booking_repository.list_expired_holds():
                trip = self.trip_repository.get_trip_for_update(booking.trip_id)
                if trip is None:
                    continue
                booking.booking_state = BookingStatus.EXPIRED.value
                self.trip_repository.release_seats(trip, booking.party_size)
                self.booking_repository.update(booking)
                emit_event(
                    DomainEvent("booking.expired", {"booking_id": booking.id, "trip_id": booking.trip_id}),
                    session=self.booking_repository.session,
                )
                expired += 1
            return expired

    @staticmethod
    def _assert_owner(booking: BookingORM, passenger_id: str) -> None:
        if booking.passenger_id != passenger_id:
            raise PermissionDeniedError("You do not have access to this booking")
