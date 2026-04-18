from datetime import UTC, datetime
from uuid import uuid4

from app.core.exceptions import (
    ConflictError,
    DomainRuleViolationError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.core.events import DomainEvent, emit_event
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.models import BookingStatus
from app.domain.bookings.state_machine import validate_transition as validate_booking_transition
from app.domain.events import DomainEventName
from app.domain.qr.models import QRTokenORM
from app.domain.qr.repository import QRRepository
from app.domain.qr.schemas import BoardingScanRequest, BoardingScanResponse
from app.domain.qr.state_machine import validate_transition as validate_qr_transition


class QRService:
    def __init__(
        self,
        qr_repository: QRRepository,
        booking_repository: BookingRepository,
    ) -> None:
        self.qr_repository = qr_repository
        self.booking_repository = booking_repository

    def issue_for_booking(self, booking_id: str) -> QRTokenORM:
        existing = self.qr_repository.get_by_booking(booking_id)
        if existing is not None:
            return existing

        token = QRTokenORM(
            id=f"qr-{uuid4().hex[:12]}",
            booking_id=booking_id,
            state="issued",
            issued_at=datetime.now(UTC),
            scanned_at=None,
        )
        self.qr_repository.save(token)
        emit_event(
            DomainEvent(
                name=DomainEventName.QR_ISSUED.value,
                payload={"qr_token_id": token.id, "booking_id": booking_id},
            ),
            session=self.qr_repository.session,
        )
        return token

    def validate_and_scan(self, request: BoardingScanRequest) -> BoardingScanResponse:
        token = self.qr_repository.get(request.qr_token_id)
        if token is None:
            raise NotFoundError("QR token not found")
        if token.state == "scanned":
            raise ConflictError("QR token already scanned")
        if token.state in {"voided", "expired"}:
            raise DomainRuleViolationError("QR token is not valid for boarding")

        booking = self.booking_repository.get(token.booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.booking_state != BookingStatus.CONFIRMED.value:
            raise InvalidStateTransitionError("Only confirmed bookings can be boarded")
        validate_booking_transition(booking.booking_state, BookingStatus.BOARDED)
        validate_qr_transition(token.state, "scanned")

        token.state = "scanned"
        token.scanned_at = datetime.now(UTC)
        self.qr_repository.save(token)

        booking.booking_state = BookingStatus.BOARDED.value
        self.booking_repository.update(booking)
        emit_event(
            DomainEvent(
                name=DomainEventName.BOOKING_BOARDED.value,
                payload={
                    "booking_id": booking.id,
                    "trip_id": booking.trip_id,
                    "stop_id": booking.origin_stop_id,
                    "timestamp": datetime.now(UTC),
                },
            ),
            session=self.qr_repository.session,
        )
        return BoardingScanResponse(
            booking_id=booking.id,
            trip_id=booking.trip_id,
            booking_state=booking.booking_state,
            qr_token_state=token.state,
        )

    def void_for_booking(self, booking_id: str) -> QRTokenORM | None:
        token = self.qr_repository.get_by_booking(booking_id)
        if token is None:
            return None
        if token.state == "scanned":
            return token
        validate_qr_transition(token.state, "voided")
        token.state = "voided"
        self.qr_repository.save(token)
        return token
