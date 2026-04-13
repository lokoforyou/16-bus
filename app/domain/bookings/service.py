from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.config import get_settings
from app.core.events import DomainEvent, emit_event
from app.domain.bookings.models import BookingORM
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.schemas import (
    BookingCancelResponse,
    BookingCreatedResponse,
    BookingDetailResponse,
    BookingPaymentResponse,
    BookingQuoteRequest,
    BookingQuoteResponse,
    CreateBookingRequest,
)
from app.domain.dispatch.service import DispatchService
from app.domain.payments.models import PaymentORM
from app.domain.payments.repository import PaymentRepository
from app.domain.payments.schemas import PaymentRequest
from app.domain.qr.service import QRService
from app.domain.trips.repository import TripRepository


class BookingService:
    def __init__(
        self,
        trip_repository: TripRepository,
        booking_repository: BookingRepository,
        payment_repository: PaymentRepository,
        qr_service: QRService,
        dispatch_service: DispatchService,
    ) -> None:
        self.trip_repository = trip_repository
        self.booking_repository = booking_repository
        self.payment_repository = payment_repository
        self.qr_service = qr_service
        self.dispatch_service = dispatch_service

    def quote(self, request: BookingQuoteRequest) -> BookingQuoteResponse:
        candidates = self.dispatch_service.find_trip_candidates(
            route_id=request.route_id,
            origin_stop_id=request.origin_stop_id,
            destination_stop_id=request.destination_stop_id,
            party_size=request.party_size,
        )
        return BookingQuoteResponse(
            candidates=[
                {
                    "trip": candidate.trip,
                    "eta_minutes": candidate.eta_minutes,
                    "estimated_fare": candidate.estimated_fare,
                }
                for candidate in candidates
            ]
        )

    def create_booking(self, request: CreateBookingRequest) -> BookingCreatedResponse:
        quote = self.quote(
            BookingQuoteRequest(
                route_id=request.route_id,
                origin_stop_id=request.origin_stop_id,
                destination_stop_id=request.destination_stop_id,
                party_size=request.party_size,
            )
        )
        if not quote.candidates:
            raise ValueError("No eligible trips found for the requested journey")

        selected_trip = quote.candidates[0]
        self.trip_repository.reserve_seats(selected_trip.trip.id, request.party_size)

        settings = get_settings()
        booking = BookingORM(
            id=f"booking-{uuid4().hex[:12]}",
            trip_id=selected_trip.trip.id,
            passenger_id=request.passenger_id,
            origin_stop_id=request.origin_stop_id,
            destination_stop_id=request.destination_stop_id,
            party_size=request.party_size,
            fare_amount=selected_trip.estimated_fare,
            hold_expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.booking_hold_minutes),
            payment_status="pending",
            booking_state="held",
            forfeiture_fee_amount=0.0,
            booking_channel=request.booking_channel,
            qr_token_id=None,
        )
        self.booking_repository.save(booking)
        emit_event(
            DomainEvent(
                name="booking.held",
                payload={"booking_id": booking.id, "trip_id": booking.trip_id},
            )
        )
        return BookingCreatedResponse(booking=booking)

    def get_booking(self, booking_id: str) -> BookingDetailResponse | None:
        booking = self.booking_repository.get(booking_id)
        if booking is None:
            return None
        return BookingDetailResponse(booking=booking)

    def pay_booking(
        self, booking_id: str, request: PaymentRequest
    ) -> BookingPaymentResponse:
        booking = self.booking_repository.get(booking_id)
        if booking is None:
            raise ValueError("Booking not found")
        if booking.booking_state == "expired":
            raise ValueError("Expired bookings cannot be paid")
        if booking.booking_state == "cancelled":
            raise ValueError("Cancelled bookings cannot be paid")
        if booking.booking_state == "confirmed":
            latest_payment = self.payment_repository.get_latest_for_booking(booking_id)
            if latest_payment is None:
                raise ValueError("Booking already confirmed")
            return BookingPaymentResponse(booking=booking, payment_id=latest_payment.id)
        if booking.booking_state != "held":
            raise ValueError("Only held bookings can be paid")

        payment = PaymentORM(
            id=f"payment-{uuid4().hex[:12]}",
            booking_id=booking.id,
            method=request.method,
            amount=booking.fare_amount,
            status="captured",
            reference=f"pay-{uuid4().hex[:16]}",
            settled_at=datetime.now(UTC),
        )
        self.payment_repository.save(payment)
        token = self.qr_service.issue_for_booking(booking.id)

        booking.payment_status = "captured"
        booking.booking_state = "confirmed"
        booking.qr_token_id = token.id
        self.booking_repository.update(booking)
        emit_event(
            DomainEvent(
                name="payment.completed",
                payload={"payment_id": payment.id, "booking_id": booking.id},
            )
        )
        emit_event(
            DomainEvent(
                name="booking.confirmed",
                payload={"booking_id": booking.id, "payment_id": payment.id},
            )
        )
        return BookingPaymentResponse(booking=booking, payment_id=payment.id)

    def cancel_booking(self, booking_id: str) -> BookingCancelResponse:
        booking = self.booking_repository.get(booking_id)
        if booking is None:
            raise ValueError("Booking not found")
        if booking.booking_state in {"cancelled", "expired"}:
            return BookingCancelResponse(booking=booking)
        if booking.booking_state == "boarded":
            raise ValueError("Boarded bookings cannot be cancelled")

        latest_payment = self.payment_repository.get_latest_for_booking(booking.id)
        if latest_payment is not None and latest_payment.status == "captured":
            latest_payment.status = "refunded"
            self.payment_repository.save(latest_payment)
            booking.payment_status = "refunded"

        booking.booking_state = "cancelled"
        self.qr_service.void_for_booking(booking.id)
        self.booking_repository.update(booking)
        self.trip_repository.release_seats(booking.trip_id, booking.party_size)
        emit_event(
            DomainEvent(
                name="booking.cancelled",
                payload={"booking_id": booking.id, "trip_id": booking.trip_id},
            )
        )
        return BookingCancelResponse(booking=booking)
