import typer

from app.tui import run_tui

app = typer.Typer(help="Interactive terminal UI")


@app.command("open")
def open_ui() -> None:
    run_tui()
