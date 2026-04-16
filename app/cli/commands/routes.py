import typer

from app.cli.output import render
from app.cli.runtime import application_services
from app.cli.session import load_session
from app.domain.routes.schemas import RouteCreate, RouteStopCreate, RouteVariantCreate

app = typer.Typer(help="Route management")


@app.command("list")
def list_routes(json_output: bool = typer.Option(False, "--json")) -> None:
    session = load_session(required=False)
    actor = session.actor if session else None
    with application_services(actor=actor) as services:
        render(services.routes.list(), json_output)


@app.command("create")
def create_route(
    id: str = typer.Option(...),
    organization_id: str = typer.Option(...),
    code: str = typer.Option(...),
    name: str = typer.Option(...),
    direction: str = typer.Option(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(
            services.routes.create(
                RouteCreate(
                    id=id,
                    organization_id=organization_id,
                    code=code,
                    name=name,
                    direction=direction,
                )
            ),
            json_output,
        )


@app.command("add-variant")
def add_variant(
    route_id: str = typer.Argument(...),
    variant_id: str = typer.Option(..., "--id"),
    name: str = typer.Option(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(services.routes.create_variant(route_id, RouteVariantCreate(id=variant_id, name=name)), json_output)


@app.command("add-stop")
def add_stop(
    route_id: str = typer.Argument(...),
    variant_id: str = typer.Argument(...),
    stop_id: str = typer.Option(...),
    sequence_number: int = typer.Option(...),
    dwell_time_seconds: int = typer.Option(60),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    session = load_session(required=True)
    with application_services(actor=session.actor) as services:
        render(
            services.routes.add_stop_to_variant(
                route_id,
                variant_id,
                RouteStopCreate(
                    stop_id=stop_id,
                    sequence_number=sequence_number,
                    dwell_time_seconds=dwell_time_seconds,
                ),
            ),
            json_output,
        )
