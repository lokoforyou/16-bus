import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.routes.schemas import StopCreate, StopUpdate

app = typer.Typer(help="Stop management")


@app.command("list")
def list_stops(
    active_only: bool = typer.Option(False),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=False)
    actor = session.actor if session else None
    with application_services(actor=actor) as services:
        render(services.stops.list(active_only), json_output)


@app.command("create")
def create_stop(
    id: str = typer.Option(...),
    name: str = typer.Option(...),
    type: str = typer.Option(...),
    lat: float = typer.Option(...),
    lon: float = typer.Option(...),
    cash_allowed: bool = typer.Option(False),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(
            services.stops.create(
                StopCreate(
                    id=id,
                    name=name,
                    type=type,
                    lat=lat,
                    lon=lon,
                    cash_allowed=cash_allowed,
                )
            ),
            json_output,
        )


@app.command("update")
def update_stop(
    stop_id: str = typer.Argument(...),
    name: str | None = typer.Option(None),
    active: bool | None = typer.Option(None),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.stops.update(stop_id, StopUpdate(name=name, active=active)), json_output)
