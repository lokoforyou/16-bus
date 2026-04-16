from app.application.context import Actor
from app.core.database import get_session_factory
from app.core.security import hash_password
from app.domain.auth.models import UserORM, UserRole
from app.domain.organizations.models import OrganizationORM, OrganizationType
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.trips.models import TripORM
from app.domain.vehicles.models import VehicleORM
from app.tui.terminal import BusctlTerminalApp


def _seed_dispatch_data() -> None:
    session = get_session_factory()()
    try:
        session.add(OrganizationORM(id="org-dsp", name="Dispatch Org", type=OrganizationType.TAXI_ASSOCIATION))
        session.add(
            UserORM(
                id="user-dsp",
                full_name="Dispatch Admin",
                phone="27050000001",
                password_hash=hash_password("pass123"),
                role=UserRole.ORG_ADMIN,
                organization_id="org-dsp",
            )
        )
        session.add(VehicleORM(id="vehicle-dsp", organization_id="org-dsp", plate_number="DSP-1", capacity=16))
        session.add(
            RouteORM(
                id="route-dsp",
                organization_id="org-dsp",
                code="DSP",
                name="Dispatch Route",
                direction="inbound",
                active=True,
            )
        )
        session.add(RouteVariantORM(id="variant-dsp", route_id="route-dsp", name="Main", active=True))
        session.add_all(
            [
                StopORM(id="stop-dsp-a", name="Stop A", type="rank", lat=0.0, lon=0.0, cash_allowed=True, active=True),
                StopORM(id="stop-dsp-b", name="Stop B", type="rank", lat=1.0, lon=1.0, cash_allowed=True, active=True),
            ]
        )
        session.add_all(
            [
                RouteStopORM(id="rs-dsp-a", route_variant_id="variant-dsp", stop_id="stop-dsp-a", sequence_number=1, dwell_time_seconds=20),
                RouteStopORM(id="rs-dsp-b", route_variant_id="variant-dsp", stop_id="stop-dsp-b", sequence_number=2, dwell_time_seconds=20),
            ]
        )
        session.add(
            TripORM(
                id="trip-dsp",
                route_id="route-dsp",
                route_variant_id="variant-dsp",
                organization_id="org-dsp",
                vehicle_id="vehicle-dsp",
                driver_id="driver-dsp",
                trip_type="rolling",
                planned_start_time=__import__("datetime").datetime.now(__import__("datetime").UTC),
                state="boarding",
                seats_total=16,
                seats_free=12,
                current_stop_id="stop-dsp-a",
            )
        )
        session.commit()
    finally:
        session.close()


def test_dispatch_board_renders_active_trips_and_events(monkeypatch) -> None:
    _seed_dispatch_data()

    app = BusctlTerminalApp(input_fn=lambda _: "quit")
    app._cached_session = type("SessionStub", (), {"actor": Actor(user_id="user-dsp", role=UserRole.ORG_ADMIN, organization_id="org-dsp", source="test")})()

    # Render once against the seeded data.
    with app._services(app._current_actor()) as services:
        renderable = app._render_dispatch_board(services)
        assert renderable is not None
        assert str(renderable.title) == "Dispatch Board"
