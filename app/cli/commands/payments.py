import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session

app = typer.Typer(help="Payment inspection")


@app.command("get")
def get_payment(
    payment_id: str = typer.Argument(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.payments.get(payment_id), json_output)
