import inspect
from enum import Enum
from typing import Any, get_args, get_origin

import click


class _ParameterInfo:
    def __init__(self, default: Any = ..., *param_decls: str, **kwargs: Any) -> None:
        self.default = default
        self.param_decls = param_decls
        self.kwargs = kwargs


class OptionInfo(_ParameterInfo):
    pass


class ArgumentInfo(_ParameterInfo):
    pass


def Option(default: Any = ..., *param_decls: str, **kwargs: Any) -> OptionInfo:
    return OptionInfo(default, *param_decls, **kwargs)


def Argument(default: Any = ..., *param_decls: str, **kwargs: Any) -> ArgumentInfo:
    return ArgumentInfo(default, *param_decls, **kwargs)


def echo(message: Any) -> None:
    click.echo(message)


def _unwrap_optional(annotation: Any) -> tuple[Any, bool]:
    origin = get_origin(annotation)
    if origin is None:
        return annotation, False
    args = [arg for arg in get_args(annotation) if arg is not type(None)]
    if len(args) == 1:
        return args[0], True
    return annotation, False


def _coerce_value(annotation: Any, value: Any) -> Any:
    if value is None or annotation is inspect._empty:
        return value
    annotation, _ = _unwrap_optional(annotation)
    if inspect.isclass(annotation) and issubclass(annotation, Enum):
        return annotation(value)
    return value


def _click_type(annotation: Any) -> Any:
    if annotation is inspect._empty:
        return None
    annotation, is_optional = _unwrap_optional(annotation)
    if inspect.isclass(annotation) and issubclass(annotation, Enum):
        return click.Choice([member.value for member in annotation], case_sensitive=False)
    if annotation is bool and is_optional:
        return click.BOOL
    if annotation in {str, int, float, bool}:
        return annotation
    return None


def _build_click_command(name: str, fn):
    signature = inspect.signature(fn)

    @click.pass_context
    def callback(ctx, **kwargs):
        converted = {
            key: _coerce_value(signature.parameters[key].annotation, value)
            for key, value in kwargs.items()
        }
        return ctx.invoke(fn, **converted)

    wrapped = callback
    for parameter in reversed(list(signature.parameters.values())):
        default = parameter.default
        annotation = parameter.annotation
        param_name = parameter.name.replace("_", "-")
        click_type = _click_type(annotation)
        if isinstance(default, OptionInfo):
            option_decls = default.param_decls or (f"--{param_name}",)
            param_decls = (parameter.name, *option_decls)
            kwargs = dict(default.kwargs)
            option_default = default.default
            if annotation is bool and option_default in {True, False}:
                kwargs.setdefault("is_flag", True)
            else:
                kwargs.setdefault("type", click_type)
            kwargs.setdefault("default", None if option_default is ... else option_default)
            wrapped = click.option(*param_decls, **kwargs)(wrapped)
        elif isinstance(default, ArgumentInfo):
            kwargs = dict(default.kwargs)
            kwargs.setdefault("type", click_type)
            if default.default is not ...:
                kwargs.setdefault("default", default.default)
                kwargs.setdefault("required", False)
            wrapped = click.argument(parameter.name, **kwargs)(wrapped)
        else:
            if default is inspect._empty:
                wrapped = click.argument(parameter.name, type=click_type)(wrapped)
            else:
                kwargs = {"default": default}
                if annotation is bool:
                    kwargs["is_flag"] = True
                else:
                    kwargs["type"] = click_type
                wrapped = click.option(parameter.name, f"--{param_name}", **kwargs)(wrapped)

    return click.command(name=name)(wrapped)


class Typer:
    def __init__(self, *, help: str | None = None) -> None:
        self._group = click.Group(help=help)

    def command(self, name: str | None = None):
        def decorator(fn):
            self._group.add_command(
                _build_click_command(name or fn.__name__.replace("_", "-"), fn)
            )
            return fn

        return decorator

    def add_typer(self, app: "Typer", name: str) -> None:
        self._group.add_command(app._group, name=name)

    def __call__(self, *args, **kwargs):
        return self._group(*args, **kwargs)
