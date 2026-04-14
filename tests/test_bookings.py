from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.database import get_session_factory
from app.core.security import hash_password
from app.domain.auth.models import UserORM, UserRole
from app.domain.bookings.models import BookingORM
from app.domain.payments.models import PaymentORM
from app.domain.qr.models import QRTokenORM
from app.domain.trips.models import TripORM


def _create_user(phone: str, role: UserRole) -> UserORM:
    session = get_session_factory()()
    try:
        user = UserORM(
            full_name=f"{role.value}-{phone}",
            phone=phone,
            password_hash=hash_password("pass123"),
            role=role,
            organization_id="org-16-bus" if role in {UserRole.ORG_ADMIN, UserRole.DRIVER} else None,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def _login(client: TestClient, phone: str) -> str:
    response = client.post("/api/v1/auth/login", json={"phone": phone, "password": "pass123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_booking(client: TestClient, token: str, **extra: object) -> str:
    payload = {
        "route_id": "route-16-soweto-jhb",
        "origin_stop_id": "stop-bara-rank",
        "destination_stop_id": "stop-town",
        "party_size": 1,
    }
    payload.update(extra)
    response = client.post("/api/v1/bookings", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    return response.json()["booking"]["id"]


def test_quote_returns_eligible_trip_candidates(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bookings/quote",
        json={
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["candidates"]) >= 1
    assert payload["candidates"][0]["trip"]["id"] == "trip-001"


def test_create_booking_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bookings",
        json={
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 1,
        },
    )
    assert response.status_code == 401


def test_create_booking_uses_session_identity_and_ignores_passenger_spoof(client: TestClient) -> None:
    user = _create_user("27811110001", UserRole.PASSENGER)
    token = _login(client, "27811110001")

    response = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "passenger_id": "forged-passenger",
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 1,
            "booking_channel": "app",
        },
    )

    assert response.status_code == 201
    assert response.json()["booking"]["passenger_id"] == user.id


def test_passenger_cannot_read_other_passenger_booking(client: TestClient) -> None:
    _create_user("27811110002", UserRole.PASSENGER)
    _create_user("27811110003", UserRole.PASSENGER)
    owner_token = _login(client, "27811110002")
    other_token = _login(client, "27811110003")

    booking_id = _create_booking(client, owner_token)

    response = client.get(f"/api/v1/bookings/{booking_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 403


def test_passenger_cannot_cancel_or_pay_other_passenger_booking(client: TestClient) -> None:
    _create_user("27811110004", UserRole.PASSENGER)
    _create_user("27811110005", UserRole.PASSENGER)
    owner_token = _login(client, "27811110004")
    attacker_token = _login(client, "27811110005")

    booking_id = _create_booking(client, owner_token)

    pay_response = client.post(
        f"/api/v1/bookings/{booking_id}/pay",
        json={"method": "card"},
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    cancel_response = client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )

    assert pay_response.status_code == 403
    assert cancel_response.status_code == 403


def test_expiry_runs_only_via_explicit_maintenance_flow(client: TestClient) -> None:
    _create_user("27811110006", UserRole.PASSENGER)
    _create_user("27811110007", UserRole.ORG_ADMIN)
    passenger_token = _login(client, "27811110006")
    admin_token = _login(client, "27811110007")

    booking_id = _create_booking(client, passenger_token, party_size=2)

    session = get_session_factory()()
    try:
        booking = session.get(BookingORM, booking_id)
        assert booking is not None
        booking.hold_expires_at = datetime.now(UTC) - timedelta(minutes=1)
        session.add(booking)
        session.commit()
    finally:
        session.close()

    detail_response = client.get(
        f"/api/v1/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["booking"]["booking_state"] == "held"

    expire_response = client.post(
        "/api/v1/bookings/maintenance/expire-holds",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert expire_response.status_code == 200
    assert expire_response.json()["expired"] >= 1

    detail_after = client.get(
        f"/api/v1/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    assert detail_after.status_code == 200
    assert detail_after.json()["booking"]["booking_state"] == "expired"


def test_cancel_and_expiry_restore_trip_seats(client: TestClient) -> None:
    _create_user("27811110008", UserRole.PASSENGER)
    _create_user("27811110009", UserRole.ORG_ADMIN)
    passenger_token = _login(client, "27811110008")
    admin_token = _login(client, "27811110009")

    # cancel path seat restoration
    booking_to_cancel = _create_booking(client, passenger_token, party_size=2)
    client.post(
        f"/api/v1/bookings/{booking_to_cancel}/pay",
        json={"method": "wallet"},
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    cancel_response = client.post(
        f"/api/v1/bookings/{booking_to_cancel}/cancel",
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    assert cancel_response.status_code == 200

    session = get_session_factory()()
    try:
        payment = session.query(PaymentORM).filter_by(booking_id=booking_to_cancel).one()
        trip = session.get(TripORM, "trip-001")
        token = session.query(QRTokenORM).filter_by(booking_id=booking_to_cancel).one()
        assert payment.status == "refunded"
        assert trip is not None
        assert trip.seats_free == 10
        assert token.state == "voided"
    finally:
        session.close()

    # expiry path seat restoration
    booking_to_expire = _create_booking(client, passenger_token, party_size=2)
    session = get_session_factory()()
    try:
        booking = session.get(BookingORM, booking_to_expire)
        assert booking is not None
        booking.hold_expires_at = datetime.now(UTC) - timedelta(minutes=1)
        session.add(booking)
        session.commit()
    finally:
        session.close()

    expire_response = client.post(
        "/api/v1/bookings/maintenance/expire-holds",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert expire_response.status_code == 200

    session = get_session_factory()()
    try:
        trip = session.get(TripORM, "trip-001")
        assert trip is not None
        assert trip.seats_free == 10
    finally:
        session.close()
