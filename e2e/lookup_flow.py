from pydantic import BaseModel

from cli_runner import CliResult
from flow_report import FlowReport


def run_lookup_flow(report: FlowReport) -> None:
    btc = CliResult.run("btc", "--json")
    summary = btc.json_output(LookupSummaryModel)
    report.require_check(
        "price btc resolves bitcoin",
        passed=btc.exit_code == 0 and summary.coin_id == "bitcoin" and summary.symbol == "btc",
        detail=f"exit {btc.exit_code}, coin_id {summary.coin_id}, price {summary.current_price}",
    )
    report.require_check(
        "price btc carries 24h change",
        passed=summary.price_change_percentage_24h is not None,
        detail=f"24h {summary.price_change_percentage_24h}",
    )

    fuzzy = CliResult.run("bitcvoin", "--json")
    fuzzy_summary = fuzzy.json_output(LookupSummaryModel)
    report.require_check(
        "price bitcvoin fuzzy-resolves bitcoin",
        passed=fuzzy.exit_code == 0 and fuzzy_summary.coin_id == "bitcoin",
        detail=f"exit {fuzzy.exit_code}, coin_id {fuzzy_summary.coin_id}",
    )

    symbol = CliResult.run("eth", "--vs", "eur")
    report.require_check(
        "price eth --vs eur prints euros",
        passed=symbol.exit_code == 0 and "€" in symbol.stdout,
        detail=f"exit {symbol.exit_code}, stdout {symbol.stdout.splitlines()[0][:60]!r}",
    )

    unknown = CliResult.run("notacoin")
    report.require_check(
        "unknown coin exits 3 with a message and no traceback",
        passed=unknown.exit_code == 3 and "no coin matches" in unknown.stdout + unknown.stderr,
        detail=f"exit {unknown.exit_code}, output {unknown.stdout.strip()[:60]!r}",
    )

    bad_currency = CliResult.run("btc", "--vs", "not-a-currency")
    report.require_check(
        "unsupported currency fails cleanly",
        passed=bad_currency.exit_code != 0 and "Traceback" not in bad_currency.stderr,
        detail=f"exit {bad_currency.exit_code}",
    )


class LookupSummaryModel(BaseModel):
    coin_id: str
    symbol: str
    current_price: float | None
    price_change_percentage_24h: float | None
