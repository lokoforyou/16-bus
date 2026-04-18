from enum import Enum


class DomainEventName(str, Enum):
    BOOKING_HELD = "booking.held"
    BOOKING_CONFIRMED = "booking.confirmed"
    BOOKING_CANCELLED = "booking.cancelled"
    BOOKING_EXPIRED = "booking.expired"
    BOOKING_BOARDED = "booking.boarded"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    TRIP_CREATED = "trip.created"
    TRIP_STATE_CHANGED = "trip.state_changed"
    TRIP_STARTED = "trip.started"
    TRIP_DEPARTED = "trip.departed"
    TRIP_COMPLETED = "trip.completed"
    QR_ISSUED = "qr.issued"
    RANK_TICKET_ISSUED = "rank.ticket.issued"
    RANK_TICKET_ASSIGNED = "rank.ticket.assigned"
    RANK_TICKET_BOARDED = "rank.ticket.boarded"
    CASH_BOOKING_AUTHORIZED = "rank.cash_booking.authorized"
