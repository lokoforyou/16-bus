from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.core.database import get_engine, get_session_factory
from app.core.security import hash_password
from app.domain.auth.models import UserORM, UserRole
from app.domain.drivers.models import DriverORM
from app.domain.organizations.models import OrganizationORM, OrganizationType
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.vehicles.models import VehicleORM


def _login(client: TestClient, phone: str, password: str = "pass123") -> str:
    response = client.post("/api/v1/auth/login", json={"phone": phone, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _seed_org_admin(phone: str = "27000000001", org_id: str = "org-16-bus") -> None:
    session = get_session_factory()()
    try:
        org = session.get(OrganizationORM, org_id)
        if org is None:
            org = OrganizationORM(id=org_id, name="Org 16", type=OrganizationType.TAXI_ASSOCIATION)
            session.add(org)
            session.flush()

        user = session.query(UserORM).filter_by(phone=phone).one_or_none()
        if user is None:
            session.add(
                UserORM(
                    full_name="Org Admin",
                    phone=phone,
                    password_hash=hash_password("pass123"),
                    role=UserRole.ORG_ADMIN,
                    organization_id=org_id,
                )
            )
        session.commit()
    finally:
        session.close()


def test_trip_and_telemetry_have_fk_links() -> None:
    inspector = inspect(get_engine())

    trip_fks = {tuple(fk["constrained_columns"]): fk["referred_table"] for fk in inspector.get_foreign_keys("trips")}
    telemetry_fks = {
        tuple(fk["constrained_columns"]): fk["referred_table"]
        for fk in inspector.get_foreign_keys("vehicle_locations")
    }

    assert trip_fks[("driver_id",)] == "drivers"
    assert trip_fks[("vehicle_id",)] == "vehicles"
    assert telemetry_fks[("vehicle_id",)] == "vehicles"


def test_route_stop_uniqueness_constraints_exist() -> None:
    inspector = inspect(get_engine())
    unique_constraints = {tuple(item["column_names"]) for item in inspector.get_unique_constraints("route_stops")}

    assert ("route_variant_id", "sequence_number") in unique_constraints
    assert ("route_variant_id", "stop_id") in unique_constraints


def test_route_stop_duplicate_sequence_and_stop_rejected(client: TestClient) -> None:
    _seed_org_admin()
    token = _login(client, "27000000001")

    dup_stop = client.post(
        "/api/v1/routes/route-16-soweto-jhb/variants/variant-16-soweto-jhb-main/stops",
        headers={"Authorization": f"Bearer {token}"},
        json={"stop_id": "stop-bara-rank", "sequence_number": 99, "dwell_time_seconds": 15},
    )
    assert dup_stop.status_code == 409

    session = get_session_factory()()
    try:
        session.add(
            StopORM(
                id="stop-new-dup-seq",
                name="Stop New",
                type="stop",
                lat=1.0,
                lon=1.0,
                cash_allowed=True,
                active=True,
            )
        )
        session.commit()
    finally:
        session.close()

    dup_seq = client.post(
        "/api/v1/routes/route-16-soweto-jhb/variants/variant-16-soweto-jhb-main/stops",
        headers={"Authorization": f"Bearer {token}"},
        json={"stop_id": "stop-new-dup-seq", "sequence_number": 1, "dwell_time_seconds": 15},
    )
    assert dup_seq.status_code == 409


def test_trip_and_shift_lifecycle_events_are_persisted(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        org = OrganizationORM(id="org-events", name="Org Events", type=OrganizationType.TAXI_ASSOCIATION)
        admin = UserORM(
            id="user-events-admin",
            full_name="Events Admin",
            phone="27000000010",
            password_hash=hash_password("pass123"),
            role=UserRole.ORG_ADMIN,
            organization_id="org-events",
        )
        driver_user = UserORM(
            id="user-events-driver",
            full_name="Events Driver",
            phone="27000000011",
            password_hash=hash_password("pass123"),
            role=UserRole.DRIVER,
            organization_id="org-events",
        )
        session.add_all([org, admin, driver_user])
        session.flush()

        driver = DriverORM(
            id="driver-events",
            organization_id="org-events",
            user_id="user-events-driver",
            full_name="Driver Events",
            phone="27000000012",
            licence_number="LEVT1",
        )
        vehicle = VehicleORM(id="vehicle-events", organization_id="org-events", plate_number="EVT-1", capacity=16)
        route = RouteORM(id="route-events", organization_id="org-events", code="EVT", name="Events Route", direction="inbound", active=True)
        variant = RouteVariantORM(id="variant-events", route_id="route-events", name="Main", active=True)
        stop = StopORM(id="stop-events", name="Stop Events", type="rank", lat=0.0, lon=0.0, cash_allowed=True, active=True)
        route_stop = RouteStopORM(id="rs-events", route_variant_id="variant-events", stop_id="stop-events", sequence_number=1, dwell_time_seconds=20)
        session.add_all([driver, vehicle, route, variant, stop, route_stop])
        session.commit()
    finally:
        session.close()

    admin_token = _login(client, "27000000010")
    driver_token = _login(client, "27000000011")

    start_shift = client.post(
        "/api/v1/driver/shifts/start",
        headers={"Authorization": f"Bearer {driver_token}"},
        json={"driver_id": "driver-events", "vehicle_id": "vehicle-events"},
    )
    assert start_shift.status_code == 200
    shift_id = start_shift.json()["id"]

    create_trip = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "id": "trip-events",
            "route_id": "route-events",
            "route_variant_id": "variant-events",
            "organization_id": "org-events",
            "vehicle_id": "vehicle-events",
            "driver_id": "driver-events",
            "trip_type": "rolling",
            "planned_start_time": datetime.now(UTC).isoformat(),
            "state": "planned",
            "seats_total": 16,
            "seats_free": 16,
            "current_stop_id": "stop-events",
        },
    )
    assert create_trip.status_code == 201

    transition = client.post(
        "/api/v1/trips/trip-events/transition?new_state=enroute",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert transition.status_code == 200

    end_shift = client.post(
        f"/api/v1/driver/shifts/{shift_id}/end",
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert end_shift.status_code == 200

    session = get_session_factory()()
    try:
        events = session.execute(text("SELECT name FROM domain_events")).scalars().all()
    finally:
        session.close()

    assert "shift.started" in events
    assert "trip.created" in events
    assert "trip.state_changed" in events
    assert "shift.ended" in events


def test_realtime_websocket_receives_trip_domain_event(client: TestClient) -> None:
    with client.websocket_connect("/api/v1/realtime/trips/trip-001") as ws:
        connected = ws.receive_json()
        assert connected["type"] == "connected"

        from app.core.events import DomainEvent, emit_event

        emit_event(DomainEvent("trip.state_changed", {"trip_id": "trip-001", "state": "enroute"}))

        event_message = ws.receive_json()
        assert event_message["type"] == "event"
        assert event_message["trip_id"] == "trip-001"
        assert event_message["event"]["name"] == "trip.state_changed"
