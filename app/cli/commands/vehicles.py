import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.vehicles.schemas import VehicleCreate

app = typer.Typer(help="Vehicle management")


@app.command("list")
def list_vehicles(
    organization_id: str | None = typer.Option(None),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.vehicles.list(organization_id), json_output)


@app.command("create")
def create_vehicle(
    organization_id: str = typer.Option(...),
    plate_number: str = typer.Option(...),
    capacity: int = typer.Option(16),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(
            services.vehicles.create(
                VehicleCreate(
                    organization_id=organization_id,
                    plate_number=plate_number,
                    capacity=capacity,
                )
            ),
            json_output,
        )
