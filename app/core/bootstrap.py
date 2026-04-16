from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.auth.models import UserORM, UserRole
from app.domain.drivers.models import DriverORM
from app.domain.organizations.models import OrganizationORM, OrganizationType
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.trips.models import TripORM
from app.domain.vehicles.models import VehicleORM


def seed_reference_data(session: Session) -> None:
    has_orgs = session.scalar(select(OrganizationORM.id).limit(1))
    if has_orgs:
        return

    org = OrganizationORM(
        id="org-16-bus",
        name="16 Bus Taxi Association",
        type=OrganizationType.TAXI_ASSOCIATION,
        compliance_status="verified",
        is_active=True,
    )
    users = [
        UserORM(
            id="user-super-admin",
            full_name="Super Admin",
            phone="27000000001",
            password_hash=hash_password("admin123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        ),
        UserORM(
            id="user-org-admin",
            full_name="Org Admin",
            phone="27000000002",
            password_hash=hash_password("org123"),
            role=UserRole.ORG_ADMIN,
            organization_id=org.id,
            is_active=True,
        ),
        UserORM(
            id="user-passenger",
            full_name="John Doe",
            phone="27000000003",
            password_hash=hash_password("user123"),
            role=UserRole.PASSENGER,
            is_active=True,
        ),
        UserORM(
            id="user-driver-001",
            full_name="Driver One",
            phone="27000000004",
            password_hash=hash_password("driver123"),
            role=UserRole.DRIVER,
            organization_id=org.id,
            is_active=True,
        ),
        UserORM(
            id="user-driver-002",
            full_name="Driver Two",
            phone="27000000005",
            password_hash=hash_password("driver123"),
            role=UserRole.DRIVER,
            organization_id=org.id,
            is_active=True,
        ),
    ]
    vehicles = [
        VehicleORM(
            id="vehicle-001",
            organization_id=org.id,
            plate_number="16B-001",
            capacity=16,
            permit_number="PERMIT-001",
            compliance_status="verified",
            is_active=True,
        ),
        VehicleORM(
            id="vehicle-002",
            organization_id=org.id,
            plate_number="16B-002",
            capacity=16,
            permit_number="PERMIT-002",
            compliance_status="verified",
            is_active=True,
        ),
    ]
    drivers = [
        DriverORM(
            id="driver-001",
            organization_id=org.id,
            user_id="user-driver-001",
            full_name="Driver One",
            phone="27000000004",
            licence_number="LIC-001",
            pdp_verified=True,
            is_active=True,
        ),
        DriverORM(
            id="driver-002",
            organization_id=org.id,
            user_id="user-driver-002",
            full_name="Driver Two",
            phone="27000000005",
            licence_number="LIC-002",
            pdp_verified=True,
            is_active=True,
        ),
    ]
    route = RouteORM(
        id="route-16-soweto-jhb",
        organization_id=org.id,
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
            organization_id=org.id,
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
            organization_id=org.id,
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

    session.add(org)
    session.add_all(users)
    session.add_all(vehicles)
    session.add_all(drivers)
    session.add(route)
    session.add(variant)
    session.add_all(stops)
    session.add_all(route_stops)
    session.add_all(trips)
    session.commit()


if __name__ == "__main__":
    import sys

    from app.core.database import get_db

    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        db_gen = get_db()
        db = next(db_gen)
        try:
            seed_reference_data(db)
            print("Database seeded successfully")
        finally:
            db.close()
