from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.database import get_session_factory
from app.domain.bookings.models import BookingORM
from app.domain.payments.models import PaymentORM
from app.domain.qr.models import QRTokenORM
from app.domain.trips.models import TripORM


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


def test_quote_rejects_invalid_stop_order_by_returning_no_candidates(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/bookings/quote",
        json={
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-town",
            "destination_stop_id": "stop-bara-rank",
            "party_size": 1,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"candidates": []}


def test_create_booking_places_hold_and_returns_booking_details(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/bookings",
        json={
            "passenger_id": "passenger-001",
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 1,
            "booking_channel": "app",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["booking"]["booking_state"] == "held"
    assert payload["booking"]["trip_id"] == "trip-001"


def test_booking_hold_expires_when_retrieved_after_expiry(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/bookings",
        json={
            "passenger_id": "passenger-002",
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
        booking.hold_expires_at = datetime.now(UTC) - timedelta(minutes=1)
        session.add(booking)
        session.commit()
    finally:
        session.close()

    response = client.get(f"/api/v1/bookings/{booking_id}")

    assert response.status_code == 200
    assert response.json()["booking"]["booking_state"] == "expired"


def test_pay_booking_confirms_booking_and_creates_payment(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/bookings",
        json={
            "passenger_id": "passenger-003",
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 1,
        },
    )
    booking_id = create_response.json()["booking"]["id"]

    pay_response = client.post(
        f"/api/v1/bookings/{booking_id}/pay",
        json={"method": "card"},
    )

    assert pay_response.status_code == 200
    payload = pay_response.json()
    assert payload["booking"]["booking_state"] == "confirmed"
    assert payload["booking"]["payment_status"] == "captured"
    assert payload["booking"]["qr_token_id"].startswith("qr-")

    payment_id = payload["payment_id"]
    payment_response = client.get(f"/api/v1/payments/{payment_id}")
    assert payment_response.status_code == 200
    assert payment_response.json()["payment"]["status"] == "captured"

    session = get_session_factory()()
    try:
        token = session.get(QRTokenORM, payload["booking"]["qr_token_id"])
        assert token is not None
        assert token.state == "issued"
    finally:
        session.close()


def test_cancel_booking_releases_seat_and_marks_refund(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/bookings",
        json={
            "passenger_id": "passenger-004",
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 2,
        },
    )
    booking_id = create_response.json()["booking"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "wallet"})

    cancel_response = client.post(f"/api/v1/bookings/{booking_id}/cancel")

    assert cancel_response.status_code == 200
    payload = cancel_response.json()
    assert payload["booking"]["booking_state"] == "cancelled"
    assert payload["booking"]["payment_status"] == "refunded"

    session = get_session_factory()()
    try:
        payment = session.query(PaymentORM).filter_by(booking_id=booking_id).one()
        trip = session.get(TripORM, payload["booking"]["trip_id"])
        assert payment.status == "refunded"
        assert trip is not None
        assert trip.seats_free == 10
        token = session.query(QRTokenORM).filter_by(booking_id=booking_id).one()
        assert token.state == "voided"
    finally:
        session.close()


def test_driver_scan_boards_confirmed_booking_and_prevents_reuse(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/bookings",
        json={
            "passenger_id": "passenger-005",
            "route_id": "route-16-soweto-jhb",
            "origin_stop_id": "stop-bara-rank",
            "destination_stop_id": "stop-town",
            "party_size": 1,
        },
    )
    booking_id = create_response.json()["booking"]["id"]
    pay_response = client.post(
        f"/api/v1/bookings/{booking_id}/pay",
        json={"method": "card"},
    )
    qr_token_id = pay_response.json()["booking"]["qr_token_id"]

    scan_response = client.post(
        "/api/v1/driver/boardings/scan",
        json={"qr_token_id": qr_token_id},
    )
    assert scan_response.status_code == 200
    assert scan_response.json()["booking_state"] == "boarded"
    assert scan_response.json()["qr_token_state"] == "scanned"

    second_scan = client.post(
        "/api/v1/driver/boardings/scan",
        json={"qr_token_id": qr_token_id},
    )
    assert second_scan.status_code == 400
    assert second_scan.json()["detail"] == "QR token already scanned"
