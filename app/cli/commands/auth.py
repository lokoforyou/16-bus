import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import clear_session, load_session, save_session
from app.domain.auth.schemas import LoginRequest

app = typer.Typer(help="Authentication commands")


@app.command("login")
def login(
    phone: str = typer.Option(...),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    with application_services() as services:
        token = services.auth.login(LoginRequest(phone=phone, password=password))
    session = save_session(token.access_token)
    render(
        {
            "access_token": token.access_token,
            "token_type": token.token_type,
            "user_id": session.user_id,
            "role": session.role,
            "organization_id": session.organization_id,
        },
        json_output,
    )


@app.command("whoami")
def whoami(json_output: bool = typer.Option(False, "--json")) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.auth.get_current_user(), json_output)


@app.command("logout")
def logout(json_output: bool = typer.Option(False, "--json")) -> None:
    clear_session()
    render({"status": "logged_out"}, json_output)
