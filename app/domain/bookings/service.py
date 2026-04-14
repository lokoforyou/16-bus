from datetime import UTC, datetime
from typing import List, Optional
from uuid import uuid4

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.bookings.models import BookingORM, BookingStatus
from app.domain.bookings.repository import BookingRepository
from app.domain.bookings.state_machine import validate_transition
from app.domain.payments.repository import PaymentRepository
from app.domain.payments.service import PaymentService
from app.domain.qr.service import QRService
from app.domain.trips.repository import TripRepository


class BookingService:
    def __init__(
        self,
        trip_repository: TripRepository,
        booking_repository: BookingRepository,
        payment_service: PaymentService,
        qr_service: QRService,
        dispatch_service: DispatchService,
    ) -> None:
        self.trip_repository = trip_repository
        self.booking_repository = booking_repository
        self.payment_service = payment_service
        self.qr_service = qr_service
        self.dispatch_service = dispatch_service

    def create_booking(
        self,
        user_id: str,
        route_id: str,
        origin_stop_id: str,
        destination_stop_id: str,
        party_size: int,
        booking_channel: str,
    ) -> BookingORM:
        candidates = self.dispatch_service.find_trip_candidates(
            route_id=route_id,
            origin_stop_id=origin_stop_id,
            destination_stop_id=destination_stop_id,
            party_size=party_size,
        )

        if not candidates:
            raise NotFoundError("No eligible trips found for the given criteria")

        # Rank candidates: earliest ETA first, then lowest fare
        candidates.sort(key=lambda c: (c.eta_minutes, c.estimated_fare))

        best_candidate = candidates[0]
        trip_id = best_candidate.trip.id

        booking = self.create_booking_hold(
            trip_id=trip_id,
            passenger_id=user_id,
            seats=party_size,
        )
        booking.booking_channel = booking_channel
        booking.fare_amount = best_candidate.estimated_fare
        return booking

    def create_booking_hold(self, trip_id: str, passenger_id: str, seats: int) -> BookingORM:
        with self.booking_repository.session.begin():
            # Lock the trip row
            trip = self.trip_repository.get_trip_for_update(trip_id)
            if not trip:
                raise NotFoundError("Trip not found")
            
            if trip.seats_free < seats:
                raise ConflictError("Not enough seats available")
                
            trip.seats_free -= seats
            self.trip_repository.update(trip)
            
            booking = BookingORM(
                id=f"booking-{uuid4().hex[:12]}",
                trip_id=trip_id,
                passenger_id=passenger_id,
                party_size=seats,
                booking_state=BookingStatus.HELD,
            )
            self.booking_repository.save(booking)
            return booking

    def confirm_booking(self, booking_id: str, payment_method: str) -> BookingORM:
        booking = self.booking_repository.get(booking_id)
        if not booking:
            raise NotFoundError("Booking not found")
        
        validate_transition(booking.booking_state, BookingStatus.CONFIRMED)
        
        # Payment handling via service
        payment = self.payment_service.process_payment(booking.fare_amount, payment_method, booking_id)
        
        booking.booking_state = BookingStatus.CONFIRMED
        self.booking_repository.update(booking)
        return booking

    def cancel_booking(self, booking_id: str) -> BookingORM:
        booking = self.booking_repository.get(booking_id)
        if not booking:
            raise NotFoundError("Booking not found")
            
        validate_transition(booking.booking_state, BookingStatus.CANCELLED)
        
        # Restore seats
        self.trip_repository.release_seats(booking.trip_id, booking.party_size)
        
        booking.booking_state = BookingStatus.CANCELLED
        self.booking_repository.update(booking)
        return booking
