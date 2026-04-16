import typer

from app.cli.output import render
from app.cli.runtime import application_services

app = typer.Typer(help="System operations")


@app.command("health")
def health(json_output: bool = typer.Option(False, "--json")) -> None:
    with application_services() as services:
        render(services.system.health(), json_output)


@app.command("seed")
def seed(json_output: bool = typer.Option(False, "--json")) -> None:
    with application_services() as services:
        render(services.system.seed(), json_output)
