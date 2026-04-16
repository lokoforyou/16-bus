import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.drivers.schemas import DriverCreate

app = typer.Typer(help="Driver management")


@app.command("list")
def list_drivers(
    organization_id: str | None = typer.Option(None),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.drivers.list(organization_id), json_output)


@app.command("create")
def create_driver(
    organization_id: str = typer.Option(...),
    user_id: str = typer.Option(...),
    full_name: str = typer.Option(...),
    phone: str = typer.Option(...),
    licence_number: str = typer.Option(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(
            services.drivers.create(
                DriverCreate(
                    organization_id=organization_id,
                    user_id=user_id,
                    full_name=full_name,
                    phone=phone,
                    licence_number=licence_number,
                )
            ),
            json_output,
        )
