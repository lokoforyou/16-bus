from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.database import get_session_factory
from app.core.security import hash_password
from app.domain.auth.models import UserORM, UserRole
from app.domain.bookings.models import BookingORM
from app.domain.organizations.models import OrganizationORM, OrganizationType
from app.domain.trips.models import TripORM


def _login(client: TestClient, phone: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"phone": phone, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_booking_repository_get_does_not_auto_expire_state(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/bookings",
        json={
            "passenger_id": "p-100",
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 1,
        },
    )
    booking_id = create_response.json()["booking"]["id"]

    session = get_session_factory()()
    try:
        booking = session.get(BookingORM, booking_id)
        assert booking is not None
        booking.hold_expires_at = datetime.now(UTC) - timedelta(minutes=10)
        session.add(booking)
        session.commit()

        fetched = session.get(BookingORM, booking_id)
        assert fetched is not None
        assert fetched.booking_state == "held"
    finally:
        session.close()


def test_overbooking_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bookings",
        json={
            "passenger_id": "p-overbook",
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 16,
        },
    )
    assert response.status_code == 400


def test_trip_create_rejects_cross_org_driver(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        org = OrganizationORM(id="org-x", name="Org X", type=OrganizationType.TAXI_ASSOCIATION)
        admin = UserORM(
            id="user-org-admin-x",
            full_name="Org Admin X",
            phone="27000000001",
            password_hash=hash_password("pass123"),
            role=UserRole.ORG_ADMIN,
            organization_id="org-x",
        )
        session.add(org)
        session.add(admin)
        session.commit()
    finally:
        session.close()

    token = _login(client, "27000000001", "pass123")

    response = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id": "trip-invalid-org",
            "route_id": "route-16-soweto-jhb",
            "route_variant_id": "variant-16-soweto-jhb-main",
            "organization_id": "org-16-bus",
            "vehicle_id": "vehicle-001",
            "driver_id": "driver-001",
            "trip_type": "rolling",
            "planned_start_time": datetime.now(UTC).isoformat(),
            "state": "planned",
            "seats_total": 16,
            "seats_free": 16,
            "current_stop_id": "stop-bara-rank",
        },
    )
    assert response.status_code == 403


def test_realtime_websocket_stays_open_for_ping_pong(client: TestClient) -> None:
    with client.websocket_connect("/api/v1/realtime/trips/trip-001") as ws:
        first = ws.receive_json()
        assert first["type"] == "connected"
        ws.send_json({"type": "ping"})
        pong = ws.receive_json()
        assert pong["type"] == "pong"


def test_expiry_restores_trip_seats(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/bookings",
        json={
            "passenger_id": "p-expire",
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 2,
        },
    )
    booking_id = create_response.json()["booking"]["id"]

    session = get_session_factory()()
    try:
        booking = session.get(BookingORM, booking_id)
        assert booking is not None
        booking.hold_expires_at = datetime.now(UTC) - timedelta(minutes=10)
        session.add(booking)
        session.commit()
    finally:
        session.close()

    detail_response = client.get(f"/api/v1/bookings/{booking_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["booking"]["booking_state"] == "expired"

    session = get_session_factory()()
    try:
        trip = session.get(TripORM, "trip-001")
        assert trip is not None
        assert trip.seats_free == 10
    finally:
        session.close()


def test_trip_create_success_with_active_shift(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        org = OrganizationORM(id="org-trip", name="Org Trip", type=OrganizationType.TAXI_ASSOCIATION)
        admin = UserORM(
            id="user-trip-admin",
            full_name="Trip Admin",
            phone="27000000002",
            password_hash=hash_password("pass123"),
            role=UserRole.ORG_ADMIN,
            organization_id="org-trip",
        )
        driver_user = UserORM(
            id="user-trip-driver",
            full_name="Trip Driver",
            phone="27000000003",
            password_hash=hash_password("pass123"),
            role=UserRole.DRIVER,
            organization_id="org-trip",
        )
        session.add_all([org, admin, driver_user])
        session.commit()

        from app.domain.drivers.models import DriverORM
        from app.domain.vehicles.models import VehicleORM

        driver = DriverORM(id="driver-trip-1", organization_id="org-trip", user_id="user-trip-driver", full_name="Trip Driver", phone="27000000013", licence_number="LT1")
        vehicle = VehicleORM(id="vehicle-trip-1", organization_id="org-trip", plate_number="TRIP-1", capacity=16)
        session.add_all([driver, vehicle])
        session.commit()

        from app.domain.routes.models import RouteORM, RouteVariantORM, StopORM, RouteStopORM
        from app.domain.shifts.models import DriverShiftORM, ShiftStatus

        route = RouteORM(id="route-trip", organization_id="org-trip", code="RTRIP", name="Route Trip", direction="inbound", active=True)
        variant = RouteVariantORM(id="variant-trip", route_id="route-trip", name="Main", active=True)
        stop = StopORM(id="stop-trip", name="Stop Trip", type="rank", lat=0.0, lon=0.0, cash_allowed=True, active=True)
        route_stop = RouteStopORM(id="rs-trip", route_variant_id="variant-trip", stop_id="stop-trip", sequence_number=1, dwell_time_seconds=60)
        shift = DriverShiftORM(id="shift-trip-1", driver_id="driver-trip-1", vehicle_id="vehicle-trip-1", organization_id="org-trip", status=ShiftStatus.ACTIVE)
        session.add_all([route, variant, stop, route_stop, shift])
        session.commit()
    finally:
        session.close()

    token = _login(client, "27000000002", "pass123")
    response = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id": "trip-valid-1",
            "route_id": "route-trip",
            "route_variant_id": "variant-trip",
            "organization_id": "org-trip",
            "vehicle_id": "vehicle-trip-1",
            "driver_id": "driver-trip-1",
            "trip_type": "rolling",
            "planned_start_time": datetime.now(UTC).isoformat(),
            "state": "planned",
            "seats_total": 16,
            "seats_free": 16,
            "current_stop_id": "stop-trip",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "trip-valid-1"
