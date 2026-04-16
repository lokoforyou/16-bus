from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from time import sleep

from fastapi.encoders import jsonable_encoder
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table

from app.application import ApplicationServices, actor_from_token_data, build_application_services
from app.cli.session import clear_session, load_session, save_session
from app.core.database import get_session_factory
from app.domain.auth.schemas import LoginRequest
from app.domain.bookings.schemas import CreateBookingRequest
from app.domain.payments.schemas import PaymentRequest
from app.domain.shifts.schemas import ShiftCreate
from app.domain.trips.models import TripStatus
from app.domain.auth.models import UserRole


@dataclass(slots=True)
class MenuResult:
    message: str


class BusctlTerminalApp:
    def __init__(
        self,
        console: Console | None = None,
        input_fn: Callable[[str], str] = input,
    ) -> None:
        self.console = console or Console()
        self.input_fn = input_fn
        self._cached_session = load_session(required=False)

    def run(self) -> None:
        self.console.print(Panel.fit("[bold]16 Bus Terminal[/bold]", subtitle="type 'help' for commands"))
        self._print_session_status()
        while True:
            command = self._prompt("busctl> ").strip().lower()
            if command in {"quit", "exit", "q"}:
                self.console.print("bye")
                return
            if command in {"help", "?"}:
                self._print_help()
            elif command == "login":
                self._login()
            elif command == "logout":
                self._logout()
            elif command == "status":
                self._print_session_status()
            elif command == "routes":
                self._show_routes()
            elif command == "stops":
                self._show_stops()
            elif command == "trips":
                self._show_trips()
            elif command == "dispatch":
                self._show_dispatch_board()
            elif command == "book":
                self._book_trip()
            elif command == "accept":
                self._accept_trip()
            elif command == "pay":
                self._pay_booking()
            elif command == "start-shift":
                self._start_shift()
            elif command == "end-shift":
                self._end_shift()
            else:
                self.console.print(f"[red]Unknown command:[/red] {command}")

    @contextmanager
    def _services(self, actor=None):
        session = get_session_factory()()
        try:
            yield build_application_services(session=session, actor=actor, request_source="cli-tui")
        finally:
            session.close()

    def _current_actor(self):
        if self._cached_session is None:
            return None
        return self._cached_session.actor

    def _prompt(self, message: str) -> str:
        return self.input_fn(message)

    def _print_help(self) -> None:
        table = Table(title="Commands")
        table.add_column("Command")
        table.add_column("Action")
        rows = [
            ("login", "Authenticate and persist a session"),
            ("logout", "Clear the current session"),
            ("status", "Show current user context"),
            ("routes", "List routes"),
            ("stops", "List stops"),
            ("trips", "List trips"),
            ("dispatch", "Open a live dispatch board"),
            ("book", "Create a booking"),
            ("accept", "Accept a trip as boarding"),
            ("pay", "Capture payment for a booking"),
            ("start-shift", "Start a driver shift"),
            ("end-shift", "End a driver shift"),
            ("quit", "Exit the terminal"),
        ]
        for command, action in rows:
            table.add_row(command, action)
        self.console.print(table)

    def _print_session_status(self) -> None:
        if self._cached_session is None:
            self.console.print("[yellow]No active session.[/yellow]")
            return
        self.console.print(
            Panel.fit(
                f"user_id={self._cached_session.user_id}\nrole={self._cached_session.role}\norganization_id={self._cached_session.organization_id}",
                title="Session",
            )
        )

    def _login(self) -> None:
        phone = self._prompt("phone: ").strip()
        password = self._prompt("password: ").strip()
        with self._services() as services:
            token = services.auth.login(LoginRequest(phone=phone, password=password))
        self._cached_session = save_session(token.access_token)
        self.console.print("[green]Logged in.[/green]")

    def _logout(self) -> None:
        clear_session()
        self._cached_session = None
        self.console.print("[green]Logged out.[/green]")

    def _show_routes(self) -> None:
        actor = self._current_actor()
        with self._services(actor) as services:
            self._print_rows("Routes", services.routes.list().items)

    def _show_stops(self) -> None:
        actor = self._current_actor()
        with self._services(actor) as services:
            self._print_rows("Stops", services.stops.list().items)

    def _show_trips(self) -> None:
        actor = self._current_actor()
        with self._services(actor) as services:
            organization_id = actor.organization_id if actor and actor.role != UserRole.SUPER_ADMIN else None
            trips = services.trips.list_active(organization_id=organization_id)
            self._print_rows("Trips", trips)

    def _show_dispatch_board(self, refresh_seconds: int = 10) -> None:
        actor = self._current_actor()
        with self._services(actor) as services:
            self.console.print("[cyan]Dispatch board active. Press Ctrl+C to stop.[/cyan]")
            try:
                with Live(self._render_dispatch_board(services), console=self.console, refresh_per_second=2) as live:
                    for _ in range(refresh_seconds):
                        live.update(self._render_dispatch_board(services))
                        sleep(1)
            except KeyboardInterrupt:
                self.console.print("[yellow]Dispatch board stopped.[/yellow]")

    def _book_trip(self) -> None:
        actor = self._current_actor()
        if actor is None:
            self.console.print("[red]Login required before booking.[/red]")
            return
        if actor.role != UserRole.PASSENGER:
            self.console.print("[red]Booking is only available for passenger accounts.[/red]")
            return
        route_id = self._prompt("route id: ").strip()
        origin_stop_id = self._prompt("origin stop id: ").strip()
        destination_stop_id = self._prompt("destination stop id: ").strip()
        party_size = int(self._prompt("party size: ").strip())
        booking_channel = self._prompt("channel [cli]: ").strip() or "cli"
        with self._services(actor) as services:
            created = services.bookings.create(
                CreateBookingRequest(
                    route_id=route_id,
                    origin_stop_id=origin_stop_id,
                    destination_stop_id=destination_stop_id,
                    party_size=party_size,
                    booking_channel=booking_channel,
                )
            )
        self._print_rows("Booking", [created.booking])

    def _accept_trip(self) -> None:
        actor = self._current_actor()
        if actor is None:
            self.console.print("[red]Login required before accepting trips.[/red]")
            return
        if actor.role not in {UserRole.DRIVER, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN}:
            self.console.print("[red]Trip acceptance is restricted to staff roles.[/red]")
            return
        trip_id = self._prompt("trip id: ").strip()
        with self._services(actor) as services:
            trip = services.trips.accept(trip_id)
        self._print_rows("Accepted Trip", [trip])

    def _pay_booking(self) -> None:
        actor = self._current_actor()
        if actor is None:
            self.console.print("[red]Login required before paying.[/red]")
            return
        if actor.role != UserRole.PASSENGER:
            self.console.print("[red]Payments are only available for passenger accounts.[/red]")
            return
        booking_id = self._prompt("booking id: ").strip()
        method = self._prompt("method [card]: ").strip() or "card"
        with self._services(actor) as services:
            result = services.bookings.pay(booking_id, PaymentRequest(method=method))
        self._print_rows("Payment", [result.booking])

    def _start_shift(self) -> None:
        actor = self._current_actor()
        if actor is None:
            self.console.print("[red]Login required before starting a shift.[/red]")
            return
        if actor.role != UserRole.DRIVER:
            self.console.print("[red]Only drivers can start shifts.[/red]")
            return
        driver_id = self._prompt("driver id: ").strip()
        vehicle_id = self._prompt("vehicle id: ").strip()
        with self._services(actor) as services:
            shift = services.shifts.start(ShiftCreate(driver_id=driver_id, vehicle_id=vehicle_id))
        self._print_rows("Shift", [shift])

    def _end_shift(self) -> None:
        actor = self._current_actor()
        if actor is None:
            self.console.print("[red]Login required before ending a shift.[/red]")
            return
        if actor.role != UserRole.DRIVER:
            self.console.print("[red]Only drivers can end shifts.[/red]")
            return
        shift_id = self._prompt("shift id: ").strip()
        with self._services(actor) as services:
            shift = services.shifts.end(shift_id)
        self._print_rows("Shift", [shift])

    def _print_rows(self, title: str, items: Iterable[Any]) -> None:
        rows = [jsonable_encoder(item) for item in items]
        table = Table(title=title)
        if not rows:
            table.add_column("empty")
            table.add_row("no rows")
            self.console.print(table)
            return
        columns = list(rows[0].keys())
        for column in columns:
            table.add_column(column)
        for row in rows:
            table.add_row(*[str(row.get(column, "")) for column in columns])
        self.console.print(table)

    def _render_dispatch_board(self, services) -> Panel:
        trips_table = Table(title="Active Trips")
        trips_table.add_column("id")
        trips_table.add_column("route")
        trips_table.add_column("state")
        trips_table.add_column("seats")
        active_trips = services.trips.list_active()
        for trip in active_trips:
            trips_table.add_row(
                trip.id,
                trip.route_id,
                trip.state,
                f"{trip.seats_free}/{trip.seats_total}",
            )

        events_table = Table(title="Recent Events")
        events_table.add_column("time")
        events_table.add_column("event")
        events_table.add_column("payload")
        for event in services.system.recent_events(limit=8):
            events_table.add_row(
                str(event["emitted_at"]),
                str(event["name"]),
                str(event["payload"]),
            )

        return Panel(
            Columns([trips_table, events_table], equal=True, expand=True),
            title="Dispatch Board",
        )


def run_tui() -> None:
    BusctlTerminalApp().run()
