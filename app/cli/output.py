import json
from pprint import pformat
from typing import Any

import typer
from fastapi.encoders import jsonable_encoder


def render(value: Any, json_output: bool = False) -> None:
    payload = jsonable_encoder(value)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    typer.echo(pformat(payload, sort_dicts=False))
