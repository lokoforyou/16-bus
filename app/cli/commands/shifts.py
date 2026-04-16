import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.shifts.schemas import ShiftCreate

app = typer.Typer(help="Shift operations")


@app.command("list")
def list_shifts(
    organization_id: str | None = typer.Option(None),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.shifts.list(organization_id), json_output)


@app.command("start")
def start_shift(
    driver_id: str = typer.Option(...),
    vehicle_id: str = typer.Option(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.shifts.start(ShiftCreate(driver_id=driver_id, vehicle_id=vehicle_id)), json_output)


@app.command("end")
def end_shift(
    shift_id: str = typer.Argument(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.shifts.end(shift_id), json_output)


@app.command("current")
def current_shift(json_output: bool = typer.Option(False, "--json")) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.shifts.current(), json_output)
