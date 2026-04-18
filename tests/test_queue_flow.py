from datetime import UTC, datetime

import pytest

from app.application import build_application_services
from app.application.context import Actor
from app.core.database import get_session_factory
from app.core.exceptions import ConflictError
from app.domain.auth.models import UserRole
from app.domain.drivers.models import DriverORM
from app.domain.organizations.models import OrganizationORM, OrganizationType
from app.domain.ranks.schemas import RankTicketAssignRequest, RankTicketIssueRequest
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.trips.models import TripORM
from app.domain.vehicles.models import VehicleORM


def _seed_queue_graph() -> None:
    session = get_session_factory()()
    try:
        session.add(OrganizationORM(id="org-queue", name="Queue Org", type=OrganizationType.TAXI_ASSOCIATION))
        session.add(
            RouteORM(
                id="route-queue",
                organization_id="org-queue",
                code="QUE",
                name="Queue Route",
                direction="inbound",
                active=True,
            )
        )
        session.add(RouteVariantORM(id="variant-queue", route_id="route-queue", name="Main", active=True))
        session.add_all(
            [
                StopORM(id="stop-queue-rank", name="Queue Rank", type="rank", lat=0.0, lon=0.0, cash_allowed=True, active=True),
                StopORM(id="stop-queue-b", name="Stop B", type="rank", lat=1.0, lon=1.0, cash_allowed=True, active=True),
            ]
        )
        session.add_all(
            [
                RouteStopORM(
                    id="rs-queue-a",
                    route_variant_id="variant-queue",
                    stop_id="stop-queue-rank",
                    sequence_number=1,
                    dwell_time_seconds=30,
                ),
                RouteStopORM(
                    id="rs-queue-b",
                    route_variant_id="variant-queue",
                    stop_id="stop-queue-b",
                    sequence_number=2,
                    dwell_time_seconds=30,
                ),
            ]
        )
        session.add(VehicleORM(id="vehicle-queue", organization_id="org-queue", plate_number="QUE-1", capacity=16))
        session.add(
            DriverORM(
                id="driver-queue",
                organization_id="org-queue",
                user_id="user-queue-driver",
                full_name="Queue Driver",
                phone="27092000001",
                licence_number="LIC-QUEUE",
            )
        )
        session.add(
            TripORM(
                id="trip-queue",
                route_id="route-queue",
                route_variant_id="variant-queue",
                organization_id="org-queue",
                vehicle_id="vehicle-queue",
                driver_id="driver-queue",
                trip_type="rolling",
                planned_start_time=datetime.now(UTC),
                state="boarding",
                seats_total=16,
                seats_free=16,
                current_stop_id="stop-queue-rank",
            )
        )
        session.commit()
    finally:
        session.close()


def test_queue_ticket_lifecycle_enforces_fifo() -> None:
    _seed_queue_graph()
    session = get_session_factory()()
    try:
        services = build_application_services(
            session=session,
            actor=Actor(user_id="marshal-queue", role=UserRole.MARSHAL, organization_id="org-queue", source="test"),
            request_source="test",
        )
        first = services.ranks.issue_ticket(RankTicketIssueRequest(rank_id="stop-queue-rank", trip_id="trip-queue"))
        second = services.ranks.issue_ticket(RankTicketIssueRequest(rank_id="stop-queue-rank", trip_id="trip-queue"))

        with pytest.raises(ConflictError):
            services.ranks.assign_ticket(
                RankTicketAssignRequest(ticket_id=second.id, trip_id="trip-queue")
            )

        assigned_first = services.ranks.assign_ticket(
            RankTicketAssignRequest(ticket_id=first.id, trip_id="trip-queue")
        )
        assert assigned_first.state == "assigned"

        boarded_first = services.ranks.board_ticket(first.id)
        assert boarded_first.state == "boarded"

        assigned_second = services.ranks.assign_ticket(
            RankTicketAssignRequest(ticket_id=second.id, trip_id="trip-queue")
        )
        assert assigned_second.state == "assigned"

        boarded_second = services.ranks.board_ticket(second.id)
        assert boarded_second.state == "boarded"
    finally:
        session.close()
