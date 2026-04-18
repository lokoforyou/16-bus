from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.config import get_settings
from app.core.events import DomainEvent, emit_event
from app.core.exceptions import ConflictError, DomainRuleViolationError, NotFoundError, PermissionDeniedError
from app.domain.events import DomainEventName
from app.domain.bookings.models import BookingORM, BookingStatus
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.schemas import (
    BookingCancelResponse,
    BookingCreatedResponse,
    BookingDetailResponse,
    BookingPaymentResponse,
    BookingQuoteRequest,
    BookingQuoteResponse,
    CreateBookingAdminRequest,
    CreateBookingRequest,
)
from app.domain.bookings.state_machine import validate_transition
from app.domain.dispatch.service import DispatchService
from app.domain.payments.schemas import PaymentRequest
from app.domain.payments.service import PaymentService
from app.domain.qr.service import QRService
from app.domain.routes.repository import RouteRepository
from app.domain.trips.repository import TripRepository


class BookingService:
    def __init__(
        self,
        trip_repository: TripRepository,
        route_repository: RouteRepository,
        booking_repository: BookingRepository,
        payment_service: PaymentService,
        qr_service: QRService,
        dispatch_service: DispatchService,
    ) -> None:
        self.trip_repository = trip_repository
        self.route_repository = route_repository
        self.booking_repository = booking_repository
        self.payment_service = payment_service
        self.qr_service = qr_service
        self.dispatch_service = dispatch_service

    def quote(self, request: BookingQuoteRequest) -> BookingQuoteResponse:
        candidates = self.dispatch_service.find_trip_candidates(
            route_id=request.route_id,
            origin_stop_id=request.origin_stop_id,
            destination_stop_id=request.destination_stop_id,
            party_size=request.party_size,
        )
        candidates.sort(key=lambda candidate: (candidate.eta_minutes, candidate.estimated_fare))
        return BookingQuoteResponse(candidates=candidates)

    def create_booking(self, request: CreateBookingRequest, passenger_id: str) -> BookingCreatedResponse:
        route = self.route_repository.get_route(request.route_id)
        if route is None:
            raise NotFoundError("Route not found")

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
        if trip.organization_id != route.organization_id:
            raise DomainRuleViolationError("Trip does not belong to the requested route owner")
        if not self.route_repository.validate_stop_order(
            trip.route_variant_id, request.origin_stop_id, request.destination_stop_id
        ):
            raise DomainRuleViolationError("Invalid stop order for route variant")

        origin_stop = self.route_repository.get_stop(request.origin_stop_id)
        if origin_stop is None:
            raise NotFoundError("Origin stop not found")
        if request.booking_channel.lower() in {"rank", "cash", "marshal"} and not origin_stop.cash_allowed:
            raise DomainRuleViolationError("Cash-at-rank bookings require a rank origin stop")

        if trip.seats_free < request.party_size:
            raise ConflictError("Not enough seats available")

        self.trip_repository.reserve_seats(trip, request.party_size)

        payment_status = "pending_cash" if request.booking_channel.lower() in {"rank", "cash", "marshal"} else "pending"
        booking = BookingORM(
            id=f"booking-{uuid4().hex[:12]}",
            trip_id=trip.id,
            passenger_id=passenger_id,
            origin_stop_id=request.origin_stop_id,
            destination_stop_id=request.destination_stop_id,
            party_size=request.party_size,
            fare_amount=quote.candidates[0].estimated_fare,
            hold_expires_at=datetime.now(UTC) + timedelta(minutes=get_settings().booking_hold_minutes),
            payment_status=payment_status,
            booking_state=BookingStatus.HELD.value,
            forfeiture_fee_amount=0.0,
            booking_channel=request.booking_channel,
            qr_token_id=None,
        )
        booking = self.booking_repository.save(booking)
        emit_event(
            DomainEvent(
                DomainEventName.BOOKING_HELD.value,
                {
                    "booking_id": booking.id,
                    "trip_id": booking.trip_id,
                    "party_size": booking.party_size,
                    "hold_expires_at": booking.hold_expires_at,
                },
            ),
            session=self.booking_repository.session,
        )
        return BookingCreatedResponse(booking=booking)

    def create_booking_admin(self, request: CreateBookingAdminRequest) -> BookingCreatedResponse:
        return self.create_booking(request, request.passenger_id)

    def get_booking(self, booking_id: str, passenger_id: str) -> BookingDetailResponse:
        booking = self.booking_repository.get(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        self._assert_owner(booking, passenger_id)
        return BookingDetailResponse(booking=booking)

    def pay_booking(
        self,
        booking_id: str,
        request: PaymentRequest,
        passenger_id: str,
    ) -> BookingPaymentResponse:
        booking = self.booking_repository.get_for_update(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        self._assert_owner(booking, passenger_id)

        validate_transition(booking.booking_state, BookingStatus.CONFIRMED)
        origin_stop = self.route_repository.get_stop(booking.origin_stop_id)
        if origin_stop is None:
            raise NotFoundError("Origin stop not found")
        if request.method == "cash":
            if booking.booking_channel not in {"rank", "cash", "marshal"} or not origin_stop.cash_allowed:
                raise DomainRuleViolationError("Cash payments are only allowed for rank-origin bookings")
            payment = self.payment_service.record_manual_payment(
                amount=booking.fare_amount,
                method=request.method,
                booking_id=booking.id,
                reference=f"cash-{booking.id}",
            )
        else:
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
            DomainEvent(
                DomainEventName.BOOKING_CONFIRMED.value,
                {
                    "booking_id": booking.id,
                    "payment_id": payment.id,
                    "passenger_id": booking.passenger_id,
                },
            ),
            session=self.booking_repository.session,
        )
        return BookingPaymentResponse(booking=booking, payment_id=payment.id)

    def cancel_booking(self, booking_id: str, passenger_id: str, operator_initiated: bool = False) -> BookingCancelResponse:
        booking = self.booking_repository.get_for_update(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if not operator_initiated:
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
        if operator_initiated:
            booking.forfeiture_fee_amount = 0.0

        self.qr_service.void_for_booking(booking.id)
        booking = self.booking_repository.update(booking)
        emit_event(
            DomainEvent(
                DomainEventName.BOOKING_CANCELLED.value,
                {
                    "booking_id": booking.id,
                    "trip_id": booking.trip_id,
                    "refund_issued": booking.payment_status == "refunded",
                    "operator_initiated": operator_initiated,
                },
            ),
            session=self.booking_repository.session,
        )
        return BookingCancelResponse(booking=booking)

    def expire_stale_holds(self) -> int:
        expired = 0
        for booking in self.booking_repository.list_expired_holds():
            trip = self.trip_repository.get_trip_for_update(booking.trip_id)
            if trip is None:
                continue
            validate_transition(booking.booking_state, BookingStatus.EXPIRED)
            booking.booking_state = BookingStatus.EXPIRED.value
            self.trip_repository.release_seats(trip, booking.party_size)
            self.booking_repository.update(booking)
            emit_event(
                DomainEvent(
                    DomainEventName.BOOKING_EXPIRED.value,
                    {"booking_id": booking.id, "trip_id": booking.trip_id},
                ),
                session=self.booking_repository.session,
            )
            expired += 1
        return expired

    def cancel_booking_as_operator(self, booking_id: str) -> BookingCancelResponse:
        booking = self.booking_repository.get_for_update(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        booking = self.cancel_booking(booking_id, booking.passenger_id, operator_initiated=True).booking
        return BookingCancelResponse(booking=booking)

    @staticmethod
    def _assert_owner(booking: BookingORM, passenger_id: str) -> None:
        if booking.passenger_id != passenger_id:
            raise PermissionDeniedError("You do not have access to this booking")
