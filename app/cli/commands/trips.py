from datetime import datetime

import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.trips.models import TripStatus
from app.domain.trips.schemas import TripCreate

app = typer.Typer(help="Trip operations")


@app.command("list")
def list_trips(
    organization_id: str | None = typer.Option(None),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=False)
    actor = session.actor if session else None
    with application_services(actor=actor) as services:
        render(services.trips.list(organization_id), json_output)


@app.command("create")
def create_trip(
    id: str = typer.Option(...),
    route_id: str = typer.Option(...),
    route_variant_id: str = typer.Option(...),
    organization_id: str = typer.Option(...),
    vehicle_id: str = typer.Option(...),
    driver_id: str = typer.Option(...),
    trip_type: str = typer.Option("rolling"),
    planned_start_time: str = typer.Option(...),
    state: str = typer.Option("planned"),
    seats_total: int = typer.Option(16),
    seats_free: int = typer.Option(16),
    current_stop_id: str = typer.Option(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(
            services.trips.create(
                TripCreate(
                    id=id,
                    route_id=route_id,
                    route_variant_id=route_variant_id,
                    organization_id=organization_id,
                    vehicle_id=vehicle_id,
                    driver_id=driver_id,
                    trip_type=trip_type,
                    planned_start_time=datetime.fromisoformat(planned_start_time),
                    state=state,
                    seats_total=seats_total,
                    seats_free=seats_free,
                    current_stop_id=current_stop_id,
                )
            ),
            json_output,
        )


@app.command("transition")
def transition_trip(
    trip_id: str = typer.Argument(...),
    new_state: TripStatus = typer.Option(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.trips.transition(trip_id, new_state), json_output)
