import httpx
import typer
from typer._click import Command as ClickCommand
from typer._click import Context as ClickContext
from typer.core import TyperGroup

from coingecko_mobile_api.coingecko.cli import register_commands
from coingecko_mobile_api.coingecko.errors import CoinNotFoundError
from coingecko_mobile_api.coingecko.rendering import console
from coingecko_mobile_api.configuration import read_application_settings
from coingecko_mobile_api.infrastructure.coingecko_api.errors import CoinGeckoApiError
from coingecko_mobile_api.shared.logging import configure_logging


class QueryDefaultingGroup(TyperGroup):
    def resolve_command(self, ctx: ClickContext, args: list[str]) -> tuple[str | None, ClickCommand | None, list[str]]:
        if args and args[0] not in self.commands:
            price_command = self.commands.get("price")
            if price_command is not None:
                return "price", price_command, args
        return super().resolve_command(ctx, args)


command_line = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    cls=QueryDefaultingGroup,
    help="CoinGecko mobile API client. `cg <query>` prices any coin; `cg --help` lists every endpoint command.",
)


@command_line.callback(invoke_without_command=True)
def default_command(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


register_commands(command_line)


def run_command_line() -> None:
    configure_logging(read_application_settings().log_level)
    try:
        command_line()
    except* CoinNotFoundError as caught:
        _fail(message=str(caught.exceptions[0]), exit_code=3)
    except* CoinGeckoApiError as caught:
        _fail(message=f"CoinGecko API error: {caught.exceptions[0]}", exit_code=2)
    except* httpx.HTTPError as caught:
        _fail(message=f"Network error: {caught.exceptions[0]}", exit_code=1)


def _fail(*, message: str, exit_code: int) -> None:
    console.print(f"[red]{message}[/]")
    raise SystemExit(exit_code)
