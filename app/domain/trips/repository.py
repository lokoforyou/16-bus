from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.trips.models import TripORM


class TripRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_active_trips(self, route_id: str | None = None) -> list[TripORM]:
        statement = select(TripORM).where(TripORM.state.in_(("planned", "boarding")))
        if route_id is not None:
            statement = statement.where(TripORM.route_id == route_id)
        statement = statement.order_by(TripORM.planned_start_time)
        return list(self.session.scalars(statement))

    def get_trip(self, trip_id: str) -> TripORM | None:
        return self.session.get(TripORM, trip_id)

    def reserve_seats(self, trip_id: str, seats: int) -> TripORM:
        trip = self.get_trip(trip_id)
        if trip is None:
            raise ValueError("Trip not found")
        if seats > trip.seats_free:
            raise ValueError("Not enough seats available")
        trip.seats_free -= seats
        self.session.add(trip)
        self.session.commit()
        self.session.refresh(trip)
        return trip

    def release_seats(self, trip_id: str, seats: int) -> TripORM:
        trip = self.get_trip(trip_id)
        if trip is None:
            raise ValueError("Trip not found")
        trip.seats_free = min(trip.seats_total, trip.seats_free + seats)
        self.session.add(trip)
        self.session.commit()
        self.session.refresh(trip)
        return trip
