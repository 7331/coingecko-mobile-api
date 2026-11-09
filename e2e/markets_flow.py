from pydantic import BaseModel, TypeAdapter

from cli_runner import CliResult
from flow_report import FlowReport


class CoinLiteModel(BaseModel):
    id: str
    symbol: str
    name: str
    market_data: CoinLiteMarketModel


class CoinLiteMarketModel(BaseModel):
    current_price: dict[str, float | None]
    market_cap_rank: int


class GlobalModel(BaseModel):
    data: GlobalDataModel


class GlobalDataModel(BaseModel):
    active_cryptocurrencies: int
    total_market_cap: dict[str, float | None]
    fear_and_greed_index: FearAndGreedModel


class FearAndGreedModel(BaseModel):
    value: int
    sentiment: str


def run_markets_flow(report: FlowReport) -> None:
    coins = CliResult.run("coins", "--per-page", "10", "--json")
    coin_list = TypeAdapter(list[CoinLiteModel]).validate_json(coins.stdout)
    first = coin_list[0] if coin_list else None
    report.require_check(
        "coins lists ten items led by bitcoin",
        passed=coins.exit_code == 0 and len(coin_list) == 10 and first is not None and first.id == "bitcoin",
        detail=f"exit {coins.exit_code}, {len(coin_list)} coins, first {first.id if first else None}",
    )

    gainers = CliResult.run("coins", "--category", "100", "--order", "h24_change_desc", "--per-page", "5")
    report.require_check(
        "gainers list prints a table",
        passed=gainers.exit_code == 0 and "Coins" in gainers.stdout,
        detail=f"exit {gainers.exit_code}",
    )

    global_result = CliResult.run("global", "--json")
    global_data = global_result.json_output(GlobalModel).data
    report.require_check(
        "global reports thousands of coins and a fear & greed index",
        passed=global_result.exit_code == 0
        and global_data.active_cryptocurrencies > 1000
        and global_data.fear_and_greed_index.value > 0,
        detail=f"exit {global_result.exit_code}, coins {global_data.active_cryptocurrencies}, "
        f"fear&greed {global_data.fear_and_greed_index.value} ({global_data.fear_and_greed_index.sentiment})",
    )

    rates = CliResult.run("rates", "eur")
    report.require_check(
        "rates filter eur shows the euro row",
        passed=rates.exit_code == 0 and "EUR" in rates.stdout,
        detail=f"exit {rates.exit_code}",
    )
