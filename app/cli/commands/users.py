import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.auth.models import UserRole
from app.domain.auth.schemas import UserCreate

app = typer.Typer(help="User management")


@app.command("list")
def list_users(
    organization_id: str | None = typer.Option(None),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.users.list_users(organization_id), json_output)


@app.command("create")
def create_user(
    full_name: str = typer.Option(...),
    phone: str = typer.Option(...),
    password: str = typer.Option(...),
    role: UserRole = typer.Option(...),
    organization_id: str | None = typer.Option(None),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        user = services.auth.register(
            UserCreate(
                full_name=full_name,
                phone=phone,
                password=password,
                role=role,
                organization_id=organization_id,
            )
        )
        render(user, json_output)
