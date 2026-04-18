from datetime import UTC, datetime

import pytest

from app.application import build_application_services
from app.application.context import Actor
from app.core.database import get_session_factory
from app.core.exceptions import DomainRuleViolationError, InvalidStateTransitionError
from app.domain.bookings.schemas import CreateBookingRequest
from app.domain.auth.models import UserRole
from app.domain.drivers.models import DriverORM
from app.domain.organizations.models import OrganizationORM, OrganizationType
from app.domain.ranks.schemas import RankCashAuthorizationRequest
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.qr.schemas import BoardingScanRequest
from app.domain.trips.models import TripORM
from app.domain.vehicles.models import VehicleORM


def _seed_graph(
    *,
    origin_type: str = "rank",
    origin_cash_allowed: bool = True,
    destination_type: str = "rank",
    vehicle_org: str = "org-gap",
    driver_org: str = "org-gap",
) -> None:
    session = get_session_factory()()
    try:
        session.add(OrganizationORM(id="org-gap", name="Gap Org", type=OrganizationType.TAXI_ASSOCIATION))
        if vehicle_org != "org-gap":
            session.add(OrganizationORM(id=vehicle_org, name="Other Org", type=OrganizationType.TAXI_ASSOCIATION))
        session.add(
            RouteORM(
                id="route-gap",
                organization_id="org-gap",
                code="GAP",
                name="Gap Route",
                direction="inbound",
                active=True,
            )
        )
        session.add(RouteVariantORM(id="variant-gap", route_id="route-gap", name="Main", active=True))
        session.add_all(
            [
                StopORM(
                    id="stop-gap-a",
                    name="Stop A",
                    type=origin_type,
                    lat=0.0,
                    lon=0.0,
                    cash_allowed=origin_cash_allowed,
                    active=True,
                ),
                StopORM(
                    id="stop-gap-b",
                    name="Stop B",
                    type=destination_type,
                    lat=1.0,
                    lon=1.0,
                    cash_allowed=True,
                    active=True,
                ),
            ]
        )
        session.add_all(
            [
                RouteStopORM(
                    id="rs-gap-a",
                    route_variant_id="variant-gap",
                    stop_id="stop-gap-a",
                    sequence_number=1,
                    dwell_time_seconds=30,
                ),
                RouteStopORM(
                    id="rs-gap-b",
                    route_variant_id="variant-gap",
                    stop_id="stop-gap-b",
                    sequence_number=2,
                    dwell_time_seconds=30,
                ),
            ]
        )
        session.add(VehicleORM(id="vehicle-gap", organization_id=vehicle_org, plate_number="GAP-1", capacity=16))
        session.add(
            DriverORM(
                id="driver-gap",
                organization_id=driver_org,
                user_id="user-gap-driver",
                full_name="Gap Driver",
                phone="27090000001",
                licence_number="LIC-GAP",
            )
        )
        session.add(
            TripORM(
                id="trip-gap",
                route_id="route-gap",
                route_variant_id="variant-gap",
                organization_id="org-gap",
                vehicle_id="vehicle-gap",
                driver_id="driver-gap",
                trip_type="rolling",
                planned_start_time=datetime.now(UTC),
                state="boarding",
                seats_total=16,
                seats_free=16,
                current_stop_id="stop-gap-a",
            )
        )
        session.commit()
    finally:
        session.close()


def test_booking_stop_order_validation() -> None:
    _seed_graph()
    session = get_session_factory()()
    try:
        services = build_application_services(
            session=session,
            actor=Actor(user_id="passenger-gap", role=UserRole.PASSENGER, organization_id=None, source="test"),
            request_source="test",
        )
        with pytest.raises(DomainRuleViolationError):
            services.bookings.create(
                CreateBookingRequest(
                    route_id="route-gap",
                    origin_stop_id="stop-gap-b",
                    destination_stop_id="stop-gap-a",
                    party_size=1,
                    booking_channel="app",
                )
            )
    finally:
        session.close()


def test_booking_requires_rank_origin_for_cash_authorization() -> None:
    _seed_graph(origin_type="stop", origin_cash_allowed=False)
    session = get_session_factory()()
    try:
        services = build_application_services(
            session=session,
            actor=Actor(user_id="passenger-gap", role="passenger", organization_id=None, source="test"),
            request_source="test",
        )
        booking = services.bookings.create(
            CreateBookingRequest(
                route_id="route-gap",
                origin_stop_id="stop-gap-a",
                destination_stop_id="stop-gap-b",
                party_size=1,
                booking_channel="app",
            )
        )

        rank_services = build_application_services(
            session=session,
            actor=Actor(user_id="marshal-gap", role=UserRole.MARSHAL, organization_id="org-gap", source="test"),
            request_source="test",
        )
        with pytest.raises(DomainRuleViolationError):
            rank_services.ranks.authorize_cash_booking(
                RankCashAuthorizationRequest(booking_id=booking.booking.id, rank_id="stop-gap-a")
            )
    finally:
        session.close()


def test_booking_cannot_board_without_confirmation() -> None:
    _seed_graph()
    session = get_session_factory()()
    try:
        services = build_application_services(
            session=session,
            actor=Actor(user_id="passenger-gap", role=UserRole.PASSENGER, organization_id=None, source="test"),
            request_source="test",
        )
        booking = services.bookings.create(
            CreateBookingRequest(
                route_id="route-gap",
                origin_stop_id="stop-gap-a",
                destination_stop_id="stop-gap-b",
                party_size=1,
                booking_channel="app",
            )
        )
        token = services.qr.service.issue_for_booking(booking.booking.id)
        qr_services = build_application_services(
            session=session,
            actor=Actor(user_id="marshal-gap", role=UserRole.MARSHAL, organization_id="org-gap", source="test"),
            request_source="test",
        )
        with pytest.raises(InvalidStateTransitionError):
            qr_services.qr.scan(BoardingScanRequest(qr_token_id=token.id))
    finally:
        session.close()
