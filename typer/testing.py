from click.testing import CliRunner as ClickCliRunner

from typer import Typer


class CliRunner(ClickCliRunner):
    def invoke(self, cli, *args, **kwargs):
        if isinstance(cli, Typer):
            cli = cli._group
        return super().invoke(cli, *args, **kwargs)
