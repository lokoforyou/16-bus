from datetime import UTC, datetime

import pytest

from app.application import build_application_services
from app.application.context import Actor
from app.core.database import get_session_factory
from app.core.exceptions import DomainRuleViolationError, InvalidStateTransitionError
from app.domain.auth.models import UserRole
from app.domain.drivers.models import DriverORM
from app.domain.organizations.models import OrganizationORM, OrganizationType
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.trips.models import TripStatus
from app.domain.trips.schemas import TripCreate
from app.domain.vehicles.models import VehicleORM


def _seed_base(vehicle_org: str = "org-trip", driver_org: str = "org-trip") -> None:
    session = get_session_factory()()
    try:
        session.add(OrganizationORM(id="org-trip", name="Trip Org", type=OrganizationType.TAXI_ASSOCIATION))
        if vehicle_org != "org-trip":
            session.add(OrganizationORM(id=vehicle_org, name="Vehicle Org", type=OrganizationType.TAXI_ASSOCIATION))
        session.add(
            RouteORM(
                id="route-trip",
                organization_id="org-trip",
                code="TRP",
                name="Trip Route",
                direction="inbound",
                active=True,
            )
        )
        session.add(RouteVariantORM(id="variant-trip", route_id="route-trip", name="Main", active=True))
        session.add_all(
            [
                StopORM(id="stop-trip-a", name="Stop A", type="rank", lat=0.0, lon=0.0, cash_allowed=True, active=True),
                StopORM(id="stop-trip-b", name="Stop B", type="rank", lat=1.0, lon=1.0, cash_allowed=True, active=True),
            ]
        )
        session.add_all(
            [
                RouteStopORM(
                    id="rs-trip-a",
                    route_variant_id="variant-trip",
                    stop_id="stop-trip-a",
                    sequence_number=1,
                    dwell_time_seconds=30,
                ),
                RouteStopORM(
                    id="rs-trip-b",
                    route_variant_id="variant-trip",
                    stop_id="stop-trip-b",
                    sequence_number=2,
                    dwell_time_seconds=30,
                ),
            ]
        )
        session.add(VehicleORM(id="vehicle-trip", organization_id=vehicle_org, plate_number="TRP-1", capacity=16))
        session.add(
            DriverORM(
                id="driver-trip",
                organization_id=driver_org,
                user_id="user-trip-driver",
                full_name="Trip Driver",
                phone="27091000001",
                licence_number="LIC-TRIP",
            )
        )
        session.commit()
    finally:
        session.close()


def test_trip_vehicle_org_mismatch_rejected() -> None:
    _seed_base(vehicle_org="org-other")
    session = get_session_factory()()
    try:
        services = build_application_services(
            session=session,
            actor=Actor(user_id="org-admin", role=UserRole.ORG_ADMIN, organization_id="org-trip", source="test"),
            request_source="test",
        )
        with pytest.raises(DomainRuleViolationError):
            services.trips.create(
                TripCreate(
                    id="trip-new",
                    route_id="route-trip",
                    route_variant_id="variant-trip",
                    organization_id="org-trip",
                    vehicle_id="vehicle-trip",
                    driver_id="driver-trip",
                    trip_type="rolling",
                    planned_start_time=datetime.now(UTC),
                    state="planned",
                    seats_total=16,
                    seats_free=16,
                    current_stop_id="stop-trip-a",
                )
            )
    finally:
        session.close()


def test_invalid_trip_state_transition_rejected() -> None:
    _seed_base()
    session = get_session_factory()()
    try:
        services = build_application_services(
            session=session,
            actor=Actor(user_id="org-admin", role=UserRole.ORG_ADMIN, organization_id="org-trip", source="test"),
            request_source="test",
        )
        trip = services.trips.create(
            TripCreate(
                id="trip-state",
                route_id="route-trip",
                route_variant_id="variant-trip",
                organization_id="org-trip",
                vehicle_id="vehicle-trip",
                driver_id="driver-trip",
                trip_type="rolling",
                planned_start_time=datetime.now(UTC),
                state="planned",
                seats_total=16,
                seats_free=16,
                current_stop_id="stop-trip-a",
            )
        )
        assert trip.state == "planned"
        with pytest.raises(InvalidStateTransitionError):
            services.trips.transition(trip.id, TripStatus.COMPLETED)
    finally:
        session.close()
