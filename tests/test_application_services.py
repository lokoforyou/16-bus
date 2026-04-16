from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from app.application import build_application_services
from app.application.context import Actor
from app.core.exceptions import PermissionDeniedError
from app.core.security import hash_password
from app.core.database import get_session_factory
from app.domain.auth.models import UserORM, UserRole
from app.domain.bookings.schemas import CreateBookingRequest
from app.domain.drivers.models import DriverORM
from app.domain.organizations.models import OrganizationORM, OrganizationType
from app.domain.payments.schemas import PaymentRequest
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.trips.models import TripORM
from app.domain.vehicles.models import VehicleORM
from app.domain.vehicles.schemas import VehicleCreate


def test_application_services_enforce_org_access_and_commit_changes() -> None:
    session = get_session_factory()()
    try:
        session.add_all(
            [
                OrganizationORM(id="org-a", name="Org A", type=OrganizationType.TAXI_ASSOCIATION),
                OrganizationORM(id="org-b", name="Org B", type=OrganizationType.TAXI_ASSOCIATION),
            ]
        )
        session.commit()
    finally:
        session.close()

    actor = Actor(user_id="admin-a", role=UserRole.ORG_ADMIN, organization_id="org-a", source="test")
    session = get_session_factory()()
    try:
        services = build_application_services(session=session, actor=actor, request_source="test")
        vehicle = services.vehicles.create(
            VehicleCreate(organization_id="org-a", plate_number="APP-001", capacity=16)
        )
        assert vehicle.organization_id == "org-a"

        with pytest.raises(PermissionDeniedError):
            services.organizations.get("org-b")
    finally:
        session.close()

    verification_session = get_session_factory()()
    try:
        persisted = verification_session.get(VehicleORM, vehicle.id)
        assert persisted is not None
        assert persisted.plate_number == "APP-001"
    finally:
        verification_session.close()


def test_booking_application_service_handles_hold_and_payment_flow() -> None:
    session = get_session_factory()()
    try:
        session.add(OrganizationORM(id="org-book", name="Org Book", type=OrganizationType.TAXI_ASSOCIATION))
        session.add(
            UserORM(
                id="user-passenger-book",
                full_name="Passenger Book",
                phone="27010000001",
                password_hash=hash_password("pass123"),
                role=UserRole.PASSENGER,
            )
        )
        session.add(
            UserORM(
                id="user-driver-book",
                full_name="Driver Book",
                phone="27010000002",
                password_hash=hash_password("pass123"),
                role=UserRole.DRIVER,
                organization_id="org-book",
            )
        )
        session.add(VehicleORM(id="vehicle-book", organization_id="org-book", plate_number="BOOK-1", capacity=16))
        session.add(
            DriverORM(
                id="driver-book",
                organization_id="org-book",
                user_id="user-driver-book",
                full_name="Driver Book",
                phone="27010000003",
                licence_number="BOOK-LIC",
            )
        )
        session.add(
            RouteORM(
                id="route-book",
                organization_id="org-book",
                code="BOOK",
                name="Booking Route",
                direction="inbound",
                active=True,
            )
        )
        session.add(RouteVariantORM(id="variant-book", route_id="route-book", name="Main", active=True))
        session.add_all(
            [
                StopORM(id="stop-book-a", name="Stop A", type="rank", lat=0.0, lon=0.0, cash_allowed=True, active=True),
                StopORM(id="stop-book-b", name="Stop B", type="rank", lat=1.0, lon=1.0, cash_allowed=True, active=True),
            ]
        )
        session.add_all(
            [
                RouteStopORM(id="rs-book-a", route_variant_id="variant-book", stop_id="stop-book-a", sequence_number=1, dwell_time_seconds=30),
                RouteStopORM(id="rs-book-b", route_variant_id="variant-book", stop_id="stop-book-b", sequence_number=2, dwell_time_seconds=30),
            ]
        )
        session.add(
            TripORM(
                id="trip-book",
                route_id="route-book",
                route_variant_id="variant-book",
                organization_id="org-book",
                vehicle_id="vehicle-book",
                driver_id="driver-book",
                trip_type="rolling",
                planned_start_time=datetime.now(UTC),
                state="boarding",
                seats_total=16,
                seats_free=16,
                current_stop_id="stop-book-a",
            )
        )
        session.commit()
    finally:
        session.close()

    actor = Actor(user_id="user-passenger-book", role=UserRole.PASSENGER, organization_id=None, source="test")
    session = get_session_factory()()
    try:
        services = build_application_services(session=session, actor=actor, request_source="test")
        created = services.bookings.create(
            CreateBookingRequest(
                route_id="route-book",
                origin_stop_id="stop-book-a",
                destination_stop_id="stop-book-b",
                party_size=1,
                booking_channel="test",
            )
        )
        paid = services.bookings.pay(created.booking.id, PaymentRequest(method="card"))
        assert paid.booking.booking_state == "confirmed"
        assert paid.booking.qr_token_id is not None
    finally:
        session.close()

    verification_session = get_session_factory()()
    try:
        booking = verification_session.execute(
            text("SELECT payment_status, qr_token_id FROM bookings WHERE id = :id"),
            {"id": created.booking.id},
        ).first()
        assert booking is not None
        assert booking.payment_status == "captured"
        assert booking.qr_token_id is not None
    finally:
        verification_session.close()
