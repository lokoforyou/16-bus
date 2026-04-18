from datetime import UTC, datetime
from uuid import uuid4

from app.core.events import DomainEvent, emit_event
from app.core.exceptions import ConflictError, DomainRuleViolationError, NotFoundError
from app.domain.bookings.models import BookingStatus
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.state_machine import validate_transition as validate_booking_transition
from app.domain.events import DomainEventName
from app.domain.payments.service import PaymentService
from app.domain.qr.service import QRService
from app.domain.ranks.models import RankQueueState, RankQueueTicketORM
from app.domain.ranks.repository import RankQueueRepository
from app.domain.ranks.schemas import (
    RankCashAuthorizationRequest,
    RankQueueTicketRead,
    RankTicketAssignRequest,
    RankTicketIssueRequest,
)
from app.domain.ranks.state_machine import validate_transition
from app.domain.routes.repository import RouteRepository
from app.domain.trips.models import TripStatus
from app.domain.trips.repository import TripRepository


class RankService:
    def __init__(
        self,
        repository: RankQueueRepository,
        booking_repository: BookingRepository,
        trip_repository: TripRepository,
        route_repository: RouteRepository,
        qr_service: QRService,
        payment_service: PaymentService,
    ) -> None:
        self.repository = repository
        self.booking_repository = booking_repository
        self.trip_repository = trip_repository
        self.route_repository = route_repository
        self.qr_service = qr_service
        self.payment_service = payment_service

    def issue_ticket(self, request: RankTicketIssueRequest) -> RankQueueTicketRead:
        stop = self.route_repository.get_stop(request.rank_id)
        if stop is None:
            raise NotFoundError("Rank not found")
        if stop.type != "rank":
            raise DomainRuleViolationError("Queue tickets can only be issued for rank stops")

        trip = None
        if request.trip_id:
            trip = self.trip_repository.get_trip_for_update(request.trip_id)
            if trip is None:
                raise NotFoundError("Trip not found")
            if trip.state not in {TripStatus.PLANNED.value, TripStatus.BOARDING.value, TripStatus.ENROUTE.value}:
                raise DomainRuleViolationError("Tickets can only be issued for active trips")
            if self.route_repository.get_stop_sequence(trip.route_variant_id, request.rank_id) is None:
                raise DomainRuleViolationError("Rank must belong to the trip route variant")

        ticket = RankQueueTicketORM(
            id=f"rank-ticket-{uuid4().hex[:12]}",
            rank_id=request.rank_id,
            trip_id=trip.id if trip else None,
            queue_number=self.repository.next_queue_number(request.rank_id),
            payment_status="pending",
            qr_token_id=None,
            state=RankQueueState.ISSUED.value,
            issued_at=datetime.now(UTC),
        )
        ticket = self.repository.save(ticket)
        emit_event(
            DomainEvent(
                DomainEventName.RANK_TICKET_ISSUED.value,
                {"ticket_id": ticket.id, "rank_id": ticket.rank_id, "trip_id": ticket.trip_id},
            ),
            session=self.repository.session,
        )
        return RankQueueTicketRead.model_validate(ticket)

    def assign_ticket(self, request: RankTicketAssignRequest) -> RankQueueTicketRead:
        ticket = self.repository.get_for_update(request.ticket_id)
        if ticket is None:
            raise NotFoundError("Rank ticket not found")
        validate_transition(ticket.state, RankQueueState.ASSIGNED.value)
        self._ensure_fifo(ticket)

        trip = self.trip_repository.get_trip_for_update(request.trip_id)
        if trip is None:
            raise NotFoundError("Trip not found")
        if self.route_repository.get_stop_sequence(trip.route_variant_id, ticket.rank_id) is None:
            raise DomainRuleViolationError("Rank ticket does not match the trip route variant")
        if trip.seats_free <= 0:
            raise ConflictError("No seats available on trip")

        ticket.trip_id = trip.id
        ticket.state = RankQueueState.ASSIGNED.value
        ticket = self.repository.save(ticket)
        emit_event(
            DomainEvent(
                DomainEventName.RANK_TICKET_ASSIGNED.value,
                {"ticket_id": ticket.id, "rank_id": ticket.rank_id, "trip_id": ticket.trip_id},
            ),
            session=self.repository.session,
        )
        return RankQueueTicketRead.model_validate(ticket)

    def board_ticket(self, ticket_id: str) -> RankQueueTicketRead:
        ticket = self.repository.get_for_update(ticket_id)
        if ticket is None:
            raise NotFoundError("Rank ticket not found")
        validate_transition(ticket.state, RankQueueState.BOARDED.value)
        self._ensure_fifo(ticket)
        ticket.state = RankQueueState.BOARDED.value
        ticket = self.repository.save(ticket)
        emit_event(
            DomainEvent(
                DomainEventName.RANK_TICKET_BOARDED.value,
                {"ticket_id": ticket.id, "rank_id": ticket.rank_id, "trip_id": ticket.trip_id},
            ),
            session=self.repository.session,
        )
        return RankQueueTicketRead.model_validate(ticket)

    def authorize_cash_booking(self, request: RankCashAuthorizationRequest) -> dict[str, object]:
        booking = self.booking_repository.get_for_update(request.booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.booking_state != BookingStatus.HELD.value:
            raise DomainRuleViolationError("Only held bookings can be authorized for cash payment")

        origin = self.route_repository.get_stop(booking.origin_stop_id)
        if origin is None:
            raise NotFoundError("Origin stop not found")
        if not origin.cash_allowed:
            raise DomainRuleViolationError("Cash bookings can only originate at rank stops")

        validate_booking_transition(booking.booking_state, BookingStatus.CONFIRMED)
        payment = self.payment_service.record_manual_payment(
            amount=booking.fare_amount,
            method="cash",
            booking_id=booking.id,
            reference=f"cash-{booking.id}",
        )
        booking.payment_status = payment.status
        booking.booking_state = BookingStatus.CONFIRMED.value
        token = self.qr_service.issue_for_booking(booking.id)
        booking.qr_token_id = token.id
        self.booking_repository.update(booking)
        emit_event(
            DomainEvent(
                DomainEventName.CASH_BOOKING_AUTHORIZED.value,
                {
                    "booking_id": booking.id,
                    "rank_id": request.rank_id,
                    "payment_id": payment.id,
                },
            ),
            session=self.repository.session,
        )
        emit_event(
            DomainEvent(
                DomainEventName.BOOKING_CONFIRMED.value,
                {"booking_id": booking.id, "payment_id": payment.id, "method": "cash"},
            ),
            session=self.repository.session,
        )
        return {
            "booking_id": booking.id,
            "payment_id": payment.id,
            "qr_token_id": token.id,
            "booking_state": booking.booking_state,
        }

    def open_trip(self, trip_id: str) -> dict[str, str]:
        trip = self.trip_repository.get_trip_for_update(trip_id)
        if trip is None:
            raise NotFoundError("Trip not found")
        if trip.state == TripStatus.PLANNED.value:
            from app.domain.trips.state_machine import validate_transition as validate_trip_transition

            validate_trip_transition(trip.state, TripStatus.BOARDING)
            trip.state = TripStatus.BOARDING.value
        elif trip.state != TripStatus.BOARDING.value:
            raise DomainRuleViolationError("Trip cannot be opened from its current state")
        self.trip_repository.update(trip)
        emit_event(
            DomainEvent(DomainEventName.TRIP_STARTED.value, {"trip_id": trip.id, "state": trip.state}),
            session=self.repository.session,
        )
        return {"trip_id": trip.id, "state": trip.state}

    def depart_trip(self, trip_id: str) -> dict[str, str]:
        trip = self.trip_repository.get_trip_for_update(trip_id)
        if trip is None:
            raise NotFoundError("Trip not found")
        from app.domain.trips.state_machine import validate_transition as validate_trip_transition

        validate_trip_transition(trip.state, TripStatus.ENROUTE)
        trip.state = TripStatus.ENROUTE.value
        self.trip_repository.update(trip)
        emit_event(
            DomainEvent(DomainEventName.TRIP_DEPARTED.value, {"trip_id": trip.id, "state": trip.state}),
            session=self.repository.session,
        )
        return {"trip_id": trip.id, "state": trip.state}

    def _ensure_fifo(self, ticket: RankQueueTicketORM) -> None:
        earliest = self.repository.get_earliest_pending(ticket.rank_id)
        if earliest is not None and earliest.id != ticket.id:
            raise ConflictError("Rank queue must be served in FIFO order")
