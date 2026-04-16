from fastapi.testclient import TestClient

from app.core.database import get_session_factory
from app.core.security import hash_password
from app.domain.auth.models import UserORM, UserRole
from app.domain.dispatch.service import PricingPolicy


def _login_passenger(client: TestClient, phone: str = "27999999001") -> str:
    session = get_session_factory()()
    try:
        user = session.query(UserORM).filter_by(phone=phone).one_or_none()
        if user is None:
            session.add(
                UserORM(
                    full_name="Booking Passenger",
                    phone=phone,
                    password_hash=hash_password("pass123"),
                    role=UserRole.PASSENGER,
                )
            )
            session.commit()
    finally:
        session.close()

    response = client.post("/api/v1/auth/login", json={"phone": phone, "password": "pass123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _login_driver(client: TestClient) -> str:
    session = get_session_factory()()
    try:
        user = session.query(UserORM).filter_by(phone="27999999010").one_or_none()
        if user is None:
            session.add(
                UserORM(
                    full_name="Booking Driver",
                    phone="27999999010",
                    password_hash=hash_password("pass123"),
                    role=UserRole.DRIVER,
                    organization_id="org-16-bus",
                )
            )
            session.commit()
    finally:
        session.close()

    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "27999999010", "password": "pass123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_driver_scan_boards_confirmed_booking_and_prevents_reuse(client: TestClient) -> None:
    token = _login_passenger(client)
    create_response = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 1,
            "booking_channel": "api_test",
        },
    )
    assert create_response.status_code == 201
    booking_id = create_response.json()["booking"]["id"]

    pay_response = client.post(
        f"/api/v1/bookings/{booking_id}/pay",
        headers={"Authorization": f"Bearer {token}"},
        json={"method": "card"},
    )
    assert pay_response.status_code == 200
    qr_token_id = pay_response.json()["booking"]["qr_token_id"]

    scan_response = client.post(
        "/api/v1/qr/scan",
        headers={"Authorization": f"Bearer {_login_driver(client)}"},
        json={"qr_token_id": qr_token_id},
    )
    assert scan_response.status_code == 200
    assert scan_response.json()["booking_state"] == "boarded"
    assert scan_response.json()["qr_token_state"] == "scanned"

    second_scan = client.post(
        "/api/v1/qr/scan",
        headers={"Authorization": f"Bearer {_login_driver(client)}"},
        json={"qr_token_id": qr_token_id},
    )
    assert second_scan.status_code == 409
    assert second_scan.json()["message"] == "QR token already scanned"


def test_pricing_policy_calculation() -> None:
    policy = PricingPolicy()
    assert policy.calculate_fare(party_size=1) == 20.5
    assert policy.calculate_fare(party_size=2) == 23.0
    assert policy.calculate_fare(party_size=4) == 28.0
    assert policy.calculate_fare(party_size=16) == 58.0


def test_create_booking_uses_ranked_trip_and_session_user(client: TestClient) -> None:
    token = _login_passenger(client, phone="27999999002")
    response = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 1,
            "booking_channel": "api_test",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["booking"]["booking_state"] == "held"
    assert payload["booking"]["trip_id"] == "trip-001"
    assert payload["booking"]["fare_amount"] == 20.5
