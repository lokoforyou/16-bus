from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.trips.models import TripORM


def seed_reference_data(session: Session) -> None:
    has_routes = session.scalar(select(RouteORM.id).limit(1))
    if has_routes:
        return

    route = RouteORM(
        id="route-16-soweto-jhb",
        organization_id="org-16-bus",
        code="16B-JHB",
        name="Soweto to Johannesburg CBD",
        direction="inbound",
        active=True,
    )
    variant = RouteVariantORM(
        id="variant-16-soweto-jhb-main",
        route_id=route.id,
        name="Main Corridor",
        active=True,
    )
    stops = [
        StopORM(
            id="stop-bara-rank",
            name="Bara Rank",
            type="rank",
            lat=-26.2594,
            lon=27.9426,
            cash_allowed=True,
            active=True,
        ),
        StopORM(
            id="stop-diepkloof",
            name="Diepkloof Interchange",
            type="stop",
            lat=-26.2452,
            lon=27.9380,
            cash_allowed=False,
            active=True,
        ),
        StopORM(
            id="stop-town",
            name="Johannesburg CBD",
            type="rank",
            lat=-26.2041,
            lon=28.0473,
            cash_allowed=True,
            active=True,
        ),
    ]
    route_stops = [
        RouteStopORM(
            id="rs-1",
            route_variant_id=variant.id,
            stop_id="stop-bara-rank",
            sequence_number=1,
            dwell_time_seconds=180,
        ),
        RouteStopORM(
            id="rs-2",
            route_variant_id=variant.id,
            stop_id="stop-diepkloof",
            sequence_number=2,
            dwell_time_seconds=120,
        ),
        RouteStopORM(
            id="rs-3",
            route_variant_id=variant.id,
            stop_id="stop-town",
            sequence_number=3,
            dwell_time_seconds=240,
        ),
    ]
    now = datetime.now(UTC)
    trips = [
        TripORM(
            id="trip-001",
            route_id=route.id,
            route_variant_id=variant.id,
            organization_id=route.organization_id,
            vehicle_id="vehicle-001",
            driver_id="driver-001",
            trip_type="rolling",
            planned_start_time=now + timedelta(minutes=8),
            state="boarding",
            seats_total=16,
            seats_free=10,
            current_stop_id="stop-bara-rank",
        ),
        TripORM(
            id="trip-002",
            route_id=route.id,
            route_variant_id=variant.id,
            organization_id=route.organization_id,
            vehicle_id="vehicle-002",
            driver_id="driver-002",
            trip_type="rolling",
            planned_start_time=now + timedelta(minutes=18),
            state="planned",
            seats_total=16,
            seats_free=14,
            current_stop_id="stop-bara-rank",
        ),
    ]

    session.add(route)
    session.add(variant)
    session.add_all(stops)
    session.add_all(route_stops)
    session.add_all(trips)
    session.commit()
