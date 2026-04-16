import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.qr.schemas import BoardingScanRequest

app = typer.Typer(help="QR operations")


@app.command("scan")
def scan_qr(
    qr_token_id: str = typer.Option(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.qr.scan(BoardingScanRequest(qr_token_id=qr_token_id)), json_output)
