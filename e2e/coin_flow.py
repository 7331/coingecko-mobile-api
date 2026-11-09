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


class ChartModel(BaseModel):
    prices: list[ChartPointModel]


class ChartPointModel(BaseModel):
    timestamp_unix_milliseconds: int
    value: float


class NewsModel(BaseModel):
    title: str
    news_site: str
    url: str


class TickerPriceDataModel(BaseModel):
    id: int
    market_name: str
    last: str
    volume_percentage: float | None


def run_coin_flow(report: FlowReport) -> None:
    detail_result = CliResult.run("coin", "bitcoin", "--json")
    detail = detail_result.json_output(CoinDetailModel)
    report.require_check(
        "coin bitcoin --json parses with market data",
        passed=detail_result.exit_code == 0 and detail.id == "bitcoin" and detail.market_data is not None,
        detail=f"exit {detail_result.exit_code}, rank {detail.market_cap_rank}",
    )

    chart = CliResult.run("chart", "btc", "--days", "30", "--json")
    chart_series = chart.json_output(ChartModel)
    chart_prices = [point.value for point in chart_series.prices]
    report.require_check(
        "chart btc 30d returns hundreds of points",
        passed=chart.exit_code == 0 and len(chart_prices) > 200,
        detail=f"exit {chart.exit_code}, {len(chart_prices)} points, first {chart_prices[0]:.2f}",
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
