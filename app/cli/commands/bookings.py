import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.bookings.schemas import BookingQuoteRequest, CreateBookingRequest
from app.domain.payments.schemas import PaymentRequest

app = typer.Typer(help="Booking operations")


@app.command("quote")
def quote_booking(
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
            services.bookings.quote(
                BookingQuoteRequest(
                    route_id=route_id,
                    origin_stop_id=origin_stop_id,
                    destination_stop_id=destination_stop_id,
                    party_size=party_size,
                )
            ),
            json_output,
        )


@app.command("create")
def create_booking(
    route_id: str = typer.Option(...),
    origin_stop_id: str = typer.Option(...),
    destination_stop_id: str = typer.Option(...),
    party_size: int = typer.Option(1),
    booking_channel: str = typer.Option("cli"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(
            services.bookings.create(
                CreateBookingRequest(
                    route_id=route_id,
                    origin_stop_id=origin_stop_id,
                    destination_stop_id=destination_stop_id,
                    party_size=party_size,
                    booking_channel=booking_channel,
                )
            ),
            json_output,
        )


@app.command("get")
def get_booking(
    booking_id: str = typer.Argument(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.bookings.get(booking_id), json_output)


@app.command("pay")
def pay_booking(
    booking_id: str = typer.Argument(...),
    method: str = typer.Option("card"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.bookings.pay(booking_id, PaymentRequest(method=method)), json_output)


@app.command("cancel")
def cancel_booking(
    booking_id: str = typer.Argument(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.bookings.cancel(booking_id), json_output)
