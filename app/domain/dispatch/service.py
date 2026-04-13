from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.routes.repository import RouteRepository
from app.domain.trips.models import TripORM
from app.domain.trips.repository import TripRepository


@dataclass(slots=True, frozen=True)
class TripCandidate:
    trip: TripORM
    eta_minutes: int
    estimated_fare: float


class DispatchService:
    def __init__(
        self,
        route_repository: RouteRepository,
        trip_repository: TripRepository,
    ) -> None:
        self.route_repository = route_repository
        self.trip_repository = trip_repository

    def find_trip_candidates(
        self,
        *,
        route_id: str,
        origin_stop_id: str,
        destination_stop_id: str,
        party_size: int,
    ) -> list[TripCandidate]:
        candidates: list[TripCandidate] = []
        for trip in self.trip_repository.list_active_trips(route_id=route_id):
            if trip.seats_free < party_size:
                continue
            if not self.route_repository.validate_stop_order(
                trip.route_variant_id, origin_stop_id, destination_stop_id
            ):
                continue

            planned_start_time = trip.planned_start_time
            if planned_start_time.tzinfo is None:
                planned_start_time = planned_start_time.replace(tzinfo=UTC)
            eta_minutes = max(
                1,
                int(
                    (
                        planned_start_time - datetime.now(UTC)
                    ).total_seconds()
                    // 60
                ),
            )
            estimated_fare = round(18.0 + (party_size * 2.5), 2)
            candidates.append(
                TripCandidate(
                    trip=trip,
                    eta_minutes=eta_minutes,
                    estimated_fare=estimated_fare,
                )
            )
        return candidates
