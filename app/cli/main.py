import typer

from app.cli.commands import (
    auth,
    bookings,
    dispatch,
    drivers,
    organizations,
    payments,
    qr,
    routes,
    shifts,
    stops,
    system,
    trips,
    users,
    vehicles,
)
from app.tui import run_tui

app = typer.Typer(help="16-bus local control plane")
app.add_typer(system.app, name="system")
app.add_typer(auth.app, name="auth")
app.add_typer(users.app, name="users")
app.add_typer(organizations.app, name="organizations")
app.add_typer(vehicles.app, name="vehicles")
app.add_typer(drivers.app, name="drivers")
app.add_typer(stops.app, name="stops")
app.add_typer(routes.app, name="routes")
app.add_typer(shifts.app, name="shifts")
app.add_typer(trips.app, name="trips")
app.add_typer(dispatch.app, name="dispatch")
app.add_typer(bookings.app, name="bookings")
app.add_typer(payments.app, name="payments")
app.add_typer(qr.app, name="qr")


@app.command("ui")
def ui() -> None:
    run_tui()


if __name__ == "__main__":
    app()
