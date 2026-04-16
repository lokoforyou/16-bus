from collections import deque
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

from rich.console import Console

from app.cli import session as cli_session
from app.core.database import get_session_factory
from app.core.security import hash_password
from app.domain.auth.models import UserORM, UserRole
from app.domain.drivers.models import DriverORM
from app.domain.organizations.models import OrganizationORM, OrganizationType
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.trips.models import TripORM
from app.domain.vehicles.models import VehicleORM


def _seed_tui_data() -> None:
    session = get_session_factory()()
    try:
        session.add(OrganizationORM(id="org-tui", name="TUI Org", type=OrganizationType.TAXI_ASSOCIATION))
        session.add(
            UserORM(
                id="user-tui-driver",
                full_name="TUI Driver",
                phone="27040000001",
                password_hash=hash_password("pass123"),
                role=UserRole.DRIVER,
                organization_id="org-tui",
            )
        )
        session.add(
            UserORM(
                id="user-tui-passenger",
                full_name="TUI Passenger",
                phone="27040000002",
                password_hash=hash_password("pass123"),
                role=UserRole.PASSENGER,
            )
        )
        session.add(DriverORM(id="driver-tui", organization_id="org-tui", user_id="user-tui-driver", full_name="TUI Driver", phone="27040000001", licence_number="LIC-TUI"))
        session.add(VehicleORM(id="vehicle-tui", organization_id="org-tui", plate_number="TUI-1", capacity=16))
        session.add(RouteORM(id="route-tui", organization_id="org-tui", code="TUI", name="TUI Route", direction="inbound", active=True))
        session.add(RouteVariantORM(id="variant-tui", route_id="route-tui", name="Main", active=True))
        session.add_all(
            [
                StopORM(id="stop-tui-a", name="Stop A", type="rank", lat=0.0, lon=0.0, cash_allowed=True, active=True),
                StopORM(id="stop-tui-b", name="Stop B", type="rank", lat=1.0, lon=1.0, cash_allowed=True, active=True),
            ]
        )
        session.add_all(
            [
                RouteStopORM(id="rs-tui-a", route_variant_id="variant-tui", stop_id="stop-tui-a", sequence_number=1, dwell_time_seconds=20),
                RouteStopORM(id="rs-tui-b", route_variant_id="variant-tui", stop_id="stop-tui-b", sequence_number=2, dwell_time_seconds=20),
            ]
        )
        session.add(
            TripORM(
                id="trip-tui",
                route_id="route-tui",
                route_variant_id="variant-tui",
                organization_id="org-tui",
                vehicle_id="vehicle-tui",
                driver_id="driver-tui",
                trip_type="rolling",
                planned_start_time=datetime.now(UTC),
                state="planned",
                seats_total=16,
                seats_free=16,
                current_stop_id="stop-tui-a",
            )
        )
        session.commit()
    finally:
        session.close()


def test_tui_can_login_and_accept_trip(monkeypatch) -> None:
    _seed_tui_data()
    temp_session_path = Path("test_tui_session.json")
    monkeypatch.setattr(cli_session, "SESSION_PATH", temp_session_path)

    inputs = deque(
        [
            "login",
            "27040000001",
            "pass123",
            "accept",
            "trip-tui",
            "quit",
        ]
    )
    captured = StringIO()
    console = Console(file=captured, force_terminal=False, color_system=None, width=120)

    def input_fn(_: str) -> str:
        return inputs.popleft()

    from app.tui.terminal import BusctlTerminalApp

    BusctlTerminalApp(console=console, input_fn=input_fn).run()

    output = captured.getvalue()
    assert "Logged in." in output
    assert "Accepted Trip" in output
    assert temp_session_path.exists()

    temp_session_path.unlink(missing_ok=True)
