from collections.abc import Sequence
from datetime import UTC, datetime

from rich.console import Console
from rich.table import Table

console = Console(highlight=False)

_SPARKLINE_CHARACTERS = "▁▂▃▄▅▆▇█"

_CURRENCY_SYMBOLS = {"usd": "$", "eur": "€", "gbp": "£", "jpy": "¥", "btc": "₿", "eth": "Ξ"}


def format_money(value: float, *, currency_code: str) -> str:
    symbol = _CURRENCY_SYMBOLS.get(currency_code, "")
    if symbol:
        return f"{symbol}{format_compact_number(value=value)}"
    return f"{format_compact_number(value=value)} {currency_code.upper()}"


def format_compact_number(*, value: float) -> str:
    magnitude = abs(value)
    sign = "-" if value < 0 else ""
    for threshold, suffix in ((1_000_000_000_000, "T"), (1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if magnitude >= threshold:
            return f"{sign}{magnitude / threshold:,.2f}{suffix}"
    if magnitude >= 1:
        return f"{sign}{magnitude:,.2f}"
    return f"{sign}{magnitude:,.6f}".rstrip("0").rstrip(".")


def format_percentage(value: float) -> str:
    arrow = "↑" if value >= 0 else "↓"
    color = "green" if value >= 0 else "red"
    return f"[{color}]{arrow} {value:+.2f}%[/]"


def format_percentage_plain(value: float) -> str:
    return f"{value:+.2f}%"


def format_timestamp_milliseconds(timestamp_unix_milliseconds: int) -> str:
    moment = datetime.fromtimestamp(timestamp_unix_milliseconds / 1000, tz=UTC)
    return moment.strftime("%Y-%m-%d %H:%M")


def render_sparkline(*, values: Sequence[float], width: int) -> str:
    if not values:
        return ""
    if len(values) <= width:
        sampled = list(values)
    else:
        bucket_count = len(values) / width
        sampled = [
            sum(values[round(bucket * bucket_count) : round((bucket + 1) * bucket_count)])
            / max(1, round((bucket + 1) * bucket_count) - round(bucket * bucket_count))
            for bucket in range(width)
        ]
    low, high = min(sampled), max(sampled)
    span = high - low or 1.0
    return "".join(
        _SPARKLINE_CHARACTERS[round((value - low) / span * (len(_SPARKLINE_CHARACTERS) - 1))] for value in sampled
    )


def print_table(*, title: str, columns: list[str], rows: list[list[str]]) -> None:
    table = Table(title=title, show_lines=False, header_style="bold")
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def print_line(line: str) -> None:
    console.print(line)
