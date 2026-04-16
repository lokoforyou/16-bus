import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.organizations.models import OrganizationType
from app.domain.organizations.schemas import OrganizationCreate

app = typer.Typer(help="Organization management")


@app.command("list")
def list_organizations(json_output: bool = typer.Option(False, "--json")) -> None:
    session = load_session(required=False)
    actor = session.actor if session else None
    with application_services(actor=actor) as services:
        render(services.organizations.list(), json_output)


@app.command("create")
def create_organization(
    name: str = typer.Option(...),
    type: OrganizationType = typer.Option(OrganizationType.TAXI_ASSOCIATION),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.organizations.create(OrganizationCreate(name=name, type=type)), json_output)
