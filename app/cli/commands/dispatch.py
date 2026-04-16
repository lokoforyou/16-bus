import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.bookings.schemas import BookingQuoteRequest

app = typer.Typer(help="Dispatch planning")


@app.command("quote")
def quote_dispatch(
    route_id: str = typer.Option(...),
    origin_stop_id: str = typer.Option(...),
    destination_stop_id: str = typer.Option(...),
    party_size: int = typer.Option(1),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=False)
    actor = session.actor if session else None
    with application_services(actor=actor) as services:
        render(
            services.dispatch.quote(
                BookingQuoteRequest(
                    route_id=route_id,
                    origin_stop_id=origin_stop_id,
                    destination_stop_id=destination_stop_id,
                    party_size=party_size,
                )
            ),
            json_output,
        )
