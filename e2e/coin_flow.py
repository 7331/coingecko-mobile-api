from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from cli_runner import CliResult
from flow_report import FlowReport


class CoinDetailModel(BaseModel):
    id: str
    symbol: str
    name: str
    market_cap_rank: int | None
    market_data: CoinMarketDataModel | None
    links: object


class CoinMarketDataModel(BaseModel):
    current_price: dict[str, float | None]
    price_change_percentage_24h: float | None
    price_change_percentage_7d: float | None
    total_volume: dict[str, float | None]
    total_supply: float | None
    max_supply: float | None


class OhlcModel(BaseModel):
    timestamp_unix_milliseconds: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float


ChartListAdapter = TypeAdapter(list[OhlcModel])


class NewsModel(BaseModel):
    title: str
    news_site: str
    url: str


class TickerPriceDataModel(BaseModel):
    id: int
    market_name: str
    last: str
    volume_percentage: float | None


def run_coin_flow(report: FlowReport, *, work_directory: Path) -> None:
    detail_result = CliResult.run("coin", "bitcoin", "--json")
    detail = detail_result.json_output(CoinDetailModel)
    report.require_check(
        "coin bitcoin --json parses with market data",
        passed=detail_result.exit_code == 0 and detail.id == "bitcoin" and detail.market_data is not None,
        detail=f"exit {detail_result.exit_code}, rank {detail.market_cap_rank}",
    )

    chart = CliResult.run("chart", "btc", "--days", "30", "--json")
    candles = ChartListAdapter.validate_json(chart.stdout)
    report.require_check(
        "chart btc 30d returns 180 candles",
        passed=chart.exit_code == 0 and len(candles) == 180,
        detail=f"exit {chart.exit_code}, {len(candles)} candles, first {candles[0].open_price:.2f}",
    )

    chart_image_path = work_directory / "chart-btc-7d.png"
    rendered = CliResult.run("chart", "btc", "--days", "7", "-o", str(chart_image_path))
    report.require_check(
        "chart btc 7d writes a candlestick png",
        passed=rendered.exit_code == 0 and chart_image_path.exists() and chart_image_path.stat().st_size > 10_000,
        detail=f"exit {rendered.exit_code}, {chart_image_path.stat().st_size if chart_image_path.exists() else 0} bytes",
    )

    rejected = CliResult.run("chart", "btc", "--days", "2")
    report.require_check(
        "chart rejects an unsupported day count cleanly",
        passed=rejected.exit_code == 2 and "days must be one of" in rejected.stderr + rejected.stdout,
        detail=f"exit {rejected.exit_code}",
    )

    markets = CliResult.run("markets", "btc")
    report.require_check(
        "markets btc prints a ticker table",
        passed=markets.exit_code == 0 and "tickers" in markets.stdout,
        detail=f"exit {markets.exit_code}",
    )

    news = CliResult.run("news", "btc", "--per-page", "5", "--json")
    articles = TypeAdapter(list[NewsModel]).validate_json(news.stdout)
    report.require_check(
        "news btc --json returns five articles with urls",
        passed=news.exit_code == 0
        and len(articles) == 5
        and all(article.url.startswith("http") for article in articles),
        detail=f"exit {news.exit_code}, first site {articles[0].news_site if articles else None}",
    )

    allocation = CliResult.run("allocation", "eth")
    report.require_check(
        "allocation eth prints allocation slices",
        passed=allocation.exit_code == 0 and "allocation" in allocation.stdout,
        detail=f"exit {allocation.exit_code}",
    )

    emissions = CliResult.run("emissions", "btc")
    report.require_check(
        "emissions btc prints a series with points",
        passed=emissions.exit_code == 0 and "points" in emissions.stdout,
        detail=f"exit {emissions.exit_code}",
    )

    financials = CliResult.run("financials", "btc", "--duration", "m1")
    report.require_check(
        "financials btc prints the fees series",
        passed=financials.exit_code == 0 and "Fees" in financials.stdout,
        detail=f"exit {financials.exit_code}",
    )

    insights = CliResult.run("insights", "bitcoin")
    report.require_check(
        "insights bitcoin returns an empty list (endpoint ships no items today)",
        passed=insights.exit_code == 0 and insights.stdout.strip() == "[]",
        detail=f"exit {insights.exit_code}, stdout {insights.stdout.strip()[:40]!r}",
    )

    categories = CliResult.run("categories", "--contains", "meme")
    report.require_check(
        "categories --contains meme finds meme categories",
        passed=categories.exit_code == 0 and "meme" in categories.stdout.lower(),
        detail=f"exit {categories.exit_code}",
    )
