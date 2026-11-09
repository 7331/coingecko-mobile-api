from contextlib import AsyncExitStack
from typing import Annotated, Literal

from pydantic import TypeAdapter
import typer
import uvloop

from coingecko_mobile_api.coingecko.chart_image import render_candlestick_chart
from coingecko_mobile_api.coingecko.composition import build_coin_gecko_service
from coingecko_mobile_api.coingecko.rendering import (
    console,
    format_compact_number,
    format_money,
    format_percentage,
    format_percentage_plain,
    format_timestamp_milliseconds,
    print_line,
    print_table,
)
from coingecko_mobile_api.coingecko.types import CoinPriceSummary, MatchKind, ResolvedCoin
from coingecko_mobile_api.infrastructure.coingecko_api.client import CoinGeckoApiClient
from coingecko_mobile_api.infrastructure.coingecko_api.enums import (
    CoinsOrder,
    CoinTickersOrder,
    TickersType,
    TokenomicsDuration,
)
from coingecko_mobile_api.infrastructure.coingecko_api.schemas import (
    CoinCategory,
    CoinInsight,
    CoinLite,
    CoinMarketData,
    CoinTickers,
    FullCoin,
    MobileCoinDetail,
    NewsArticle,
    OhlcPoint,
    TickerPriceData,
    TokenomicsEmissionsSeries,
    TokenomicsFinancialsSeries,
)

QueryArgument = Annotated[
    str, typer.Argument(help="Coin id, symbol or name, exact or fuzzy, for example bitcoin, BTC or bitcvoin")
]
JsonOption = Annotated[bool, typer.Option("--json", help="Print the full model as JSON instead of a table")]

_COIN_LITE_LIST_ADAPTER = TypeAdapter(list[CoinLite])
_FULL_COIN_LIST_ADAPTER = TypeAdapter(list[FullCoin])
_NEWS_LIST_ADAPTER = TypeAdapter(list[NewsArticle])
_INSIGHT_LIST_ADAPTER = TypeAdapter(list[CoinInsight])
_CATEGORY_LIST_ADAPTER = TypeAdapter(list[CoinCategory])
_EMISSIONS_LIST_ADAPTER = TypeAdapter(list[TokenomicsEmissionsSeries])
_FINANCIALS_LIST_ADAPTER = TypeAdapter(list[TokenomicsFinancialsSeries])
_OHLC_LIST_ADAPTER = TypeAdapter(list[OhlcPoint])

_RESOLVED_MATCH_KINDS = (MatchKind.PREFIX, MatchKind.FUZZY, MatchKind.API_SEARCH)


def register_commands(command_line: typer.Typer) -> None:
    command_line.command(name="price")(price_command)
    command_line.command(name="coins")(coins_command)
    command_line.command(name="global")(global_command)
    command_line.command(name="search")(search_command)
    command_line.command(name="coin")(coin_command)
    command_line.command(name="chart")(chart_command)
    command_line.command(name="markets")(markets_command)
    command_line.command(name="ticker")(ticker_command)
    command_line.command(name="rates")(rates_command)
    command_line.command(name="news")(news_command)
    command_line.command(name="insights")(insights_command)
    command_line.command(name="categories")(categories_command)
    command_line.command(name="allocation")(allocation_command)
    command_line.command(name="emissions")(emissions_command)
    command_line.command(name="financials")(financials_command)


def price_command(
    query: QueryArgument,
    vs_currency: Annotated[str, typer.Option("--vs")] = "usd",
    as_json: JsonOption = False,
) -> None:
    run_price(query=query, vs_currency=vs_currency, as_json=as_json)


def run_price(*, query: str, vs_currency: str = "usd", as_json: bool = False) -> None:
    uvloop.run(_price(query=query, vs_currency=vs_currency, as_json=as_json))


async def _price(*, query: str, vs_currency: str, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        service = build_coin_gecko_service(exit_stack=exit_stack)
        summary = await service.coin_price_summary(query=query, vs_currency=vs_currency)
    if as_json:
        typer.echo(summary.model_dump_json(indent=2))
    else:
        _render_price_summary(summary=summary)


def coins_command(
    vs_currency: Annotated[str, typer.Option("--vs")] = "usd",
    category_id: Annotated[str, typer.Option("--category")] = "300",
    page: Annotated[int, typer.Option("--page", min=1)] = 1,
    per_page: Annotated[int, typer.Option("--per-page", min=1, max=300)] = 25,
    locale: Annotated[str, typer.Option("--locale")] = "en",
    order: Annotated[CoinsOrder, typer.Option("--order")] = CoinsOrder.MARKET_CAP_DESC,
    multiple_currencies: Annotated[bool, typer.Option("--multiple-currencies")] = False,
    full: Annotated[
        bool, typer.Option("--full", help="Fetch the plain v3 shape instead of the slim mobile shape")
    ] = False,
    as_json: JsonOption = False,
) -> None:
    uvloop.run(
        _coins(
            vs_currency=vs_currency,
            category_id=category_id,
            page=page,
            per_page=per_page,
            locale=locale,
            order=order,
            multiple_currencies=multiple_currencies,
            full=full,
            as_json=as_json,
        )
    )


async def _coins(
    *,
    vs_currency: str,
    category_id: str,
    page: int,
    per_page: int,
    locale: str,
    order: CoinsOrder,
    multiple_currencies: bool,
    full: bool,
    as_json: bool,
) -> None:
    async with AsyncExitStack() as exit_stack:
        client = CoinGeckoApiClient.open(exit_stack=exit_stack)
        if full:
            coins = await client.list_market_coins_full(
                vs_currency=vs_currency,
                category_id=category_id,
                page=page,
                per_page=per_page,
                locale=locale,
                order=order,
                multiple_currencies=multiple_currencies,
            )
            if as_json:
                typer.echo(_FULL_COIN_LIST_ADAPTER.dump_json(coins, by_alias=True, indent=2).decode())
                return
        else:
            coins = await client.list_market_coins(
                vs_currency=vs_currency,
                category_id=category_id,
                page=page,
                per_page=per_page,
                locale=locale,
                order=order,
                multiple_currencies=multiple_currencies,
            )
            if as_json:
                typer.echo(_COIN_LITE_LIST_ADAPTER.dump_json(coins, by_alias=True, indent=2).decode())
                return
    currency = vs_currency.lower()
    rows = [
        [
            str(coin.market_data.market_cap_rank),
            coin.symbol.upper(),
            coin.name,
            _optional_price(coin.market_data.current_price.get(currency), vs_currency=currency),
            _optional_percentage(coin.market_data.price_change_percentage_1h_in_currency.get(currency)),
            _optional_percentage(coin.market_data.price_change_percentage_24h_in_currency.get(currency)),
            _optional_percentage(coin.market_data.price_change_percentage_7d_in_currency.get(currency)),
            _optional_price(coin.market_data.market_cap.get(currency), vs_currency=currency),
        ]
        for coin in coins
    ]
    print_table(
        title=f"Coins · {category_id} · page {page} · {len(coins)} items",
        columns=["#", "Symbol", "Name", "Price", "1h", "24h", "7d", "Market cap"],
        rows=rows,
    )


def global_command(
    as_json: JsonOption = False, vs_currency: Annotated[str | None, typer.Option("--vs")] = None
) -> None:
    uvloop.run(_global(as_json=as_json, vs_currency=vs_currency))


async def _global(*, as_json: bool, vs_currency: str | None) -> None:
    async with AsyncExitStack() as exit_stack:
        client = CoinGeckoApiClient.open(exit_stack=exit_stack)
        response = await client.fetch_global_market_data(vs_currency=vs_currency)
    if as_json:
        typer.echo(response.model_dump_json(by_alias=True, indent=2))
    else:
        data = response.data
        usd_dominance = data.market_cap_percentage.get("usd")
        print_line(
            f"[bold]Global market[/] · {data.active_cryptocurrencies:,} coins · {data.markets:,} exchanges · "
            f"fear & greed {data.fear_and_greed_index.value} ({data.fear_and_greed_index.sentiment})"
        )
        print_line(
            f"Total market cap {format_money(data.total_market_cap.get('usd') or 0.0, currency_code='usd')} "
            f"{format_percentage(data.market_cap_change_percentage_24h_usd)} · "
            f"volume {format_money(data.total_volume.get('usd') or 0.0, currency_code='usd')} "
            f"{format_percentage(data.volume_change_percentage_24h_usd)}"
            + (f" · BTC dominance {usd_dominance:.1f}%" if usd_dominance is not None else "")
        )
        dominance_rows = [
            [code.upper(), f"{share:.2f}%"]
            for code, share in sorted(data.market_cap_percentage.items(), key=lambda pair: -(pair[1] or 0.0))[:5]
        ]
        print_table(title="Dominance", columns=["Coin", "Share"], rows=dominance_rows)


def search_command(
    query: Annotated[str, typer.Argument(help="Search text")],
    vs_currency: Annotated[str, typer.Option("--vs")] = "usd",
    locale: Annotated[str, typer.Option("--locale")] = "en",
    as_json: JsonOption = False,
) -> None:
    uvloop.run(_search(query=query, vs_currency=vs_currency, locale=locale, as_json=as_json))


async def _search(*, query: str, vs_currency: str, locale: str, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        client = CoinGeckoApiClient.open(exit_stack=exit_stack)
        results = await client.search(query=query, vs_currency=vs_currency, locale=locale)
    if as_json:
        typer.echo(results.model_dump_json(by_alias=True, indent=2))
    else:
        currency = vs_currency.lower()
        rows = [
            [
                str(coin.market_cap_rank) if coin.market_cap_rank is not None else "-",
                coin.symbol.upper(),
                coin.name,
                _optional_price(coin.data.price, vs_currency=currency),
                _optional_percentage(coin.data.price_change_percentage_24h),
            ]
            for coin in results.coins[:15]
        ]
        print_table(
            title=f"Search {query!r} · {len(results.coins)} coins, {len(results.rwas)} RWAs, "
            f"{len(results.nft_contracts)} NFTs, {len(results.markets)} exchanges, {len(results.categories)} categories",
            columns=["#", "Symbol", "Name", "Price", "24h"],
            rows=rows,
        )


def coin_command(
    query: QueryArgument,
    localization: Annotated[bool, typer.Option("--localization/--no-localization")] = True,
    tickers: Annotated[bool, typer.Option("--tickers/--no-tickers")] = False,
    market_data: Annotated[bool, typer.Option("--market-data/--no-market-data")] = True,
    community_data: Annotated[bool, typer.Option("--community/--no-community")] = True,
    developer_data: Annotated[bool, typer.Option("--developer/--no-developer")] = True,
    sparkline: Annotated[bool, typer.Option("--sparkline/--no-sparkline")] = False,
    include_categories_details: Annotated[bool, typer.Option("--categories-details/--no-categories-details")] = True,
    as_json: JsonOption = False,
) -> None:
    uvloop.run(
        _coin(
            query=query,
            localization=localization,
            tickers=tickers,
            market_data=market_data,
            community_data=community_data,
            developer_data=developer_data,
            sparkline=sparkline,
            include_categories_details=include_categories_details,
            as_json=as_json,
        )
    )


async def _coin(
    *,
    query: str,
    localization: bool,
    tickers: bool,
    market_data: bool,
    community_data: bool,
    developer_data: bool,
    sparkline: bool,
    include_categories_details: bool,
    as_json: bool,
) -> None:
    async with AsyncExitStack() as exit_stack:
        service = build_coin_gecko_service(exit_stack=exit_stack)
        resolved = await service.resolve_coin(query=query)
        detail = await service.client.fetch_coin(
            coin_id=resolved.coin_id,
            localization=localization,
            tickers=tickers,
            market_data=market_data,
            community_data=community_data,
            developer_data=developer_data,
            sparkline=sparkline,
            include_exchange_logo=True,
            include_categories_details=include_categories_details,
            include_chain_logo=True,
        )
    _print_resolution(resolved=resolved, query=query, as_json=as_json)
    if as_json:
        typer.echo(detail.model_dump_json(by_alias=True, indent=2))
    else:
        _render_coin_detail(detail=detail)


def chart_command(
    query: QueryArgument,
    vs_currency: Annotated[str, typer.Option("--vs")] = "usd",
    days: Annotated[str, typer.Option("--days", help="One of 1, 7, 14, 30, 90, 180, 365 or max")] = "1",
    output_path: Annotated[
        str | None, typer.Option("-o", "--output", help="Image path; defaults to ./<coin>-<days>.png")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    uvloop.run(_chart(query=query, vs_currency=vs_currency, days=days, output_path=output_path, as_json=as_json))


async def _chart(*, query: str, vs_currency: str, days: str, output_path: str | None, as_json: bool) -> None:
    parsed_days = _parse_ohlc_days(raw_days=days)
    async with AsyncExitStack() as exit_stack:
        service = build_coin_gecko_service(exit_stack=exit_stack)
        resolved = await service.resolve_coin(query=query)
        candles = await service.client.fetch_coin_ohlc(
            coin_id=resolved.coin_id, vs_currency=vs_currency, days=parsed_days
        )
    _print_resolution(resolved=resolved, query=query, as_json=as_json)
    if as_json:
        typer.echo(_OHLC_LIST_ADAPTER.dump_json(candles, by_alias=True, indent=2).decode())
        return
    image_path = output_path if output_path is not None else f"{resolved.coin_id}-{days}.png"
    render_candlestick_chart(
        candles=candles,
        coin_name=resolved.name,
        days_label=_days_label(days=days),
        vs_currency=vs_currency,
        output_path=image_path,
    )
    print_line(f"[bold]{len(candles)} candles[/] -> {image_path}")


def markets_command(
    query: QueryArgument,
    exchanges_ids: Annotated[str, typer.Option("--exchanges")] = "",
    order: Annotated[CoinTickersOrder, typer.Option("--order")] = CoinTickersOrder.TRUST_SCORE_DESC,
    page: Annotated[int, typer.Option("--page", min=1)] = 1,
    tickers_type: Annotated[TickersType, typer.Option("--type")] = TickersType.SPOT,
    as_json: JsonOption = False,
) -> None:
    uvloop.run(
        _markets(
            query=query, exchanges_ids=exchanges_ids, order=order, page=page, tickers_type=tickers_type, as_json=as_json
        )
    )


async def _markets(
    *, query: str, exchanges_ids: str, order: CoinTickersOrder, page: int, tickers_type: TickersType, as_json: bool
) -> None:
    async with AsyncExitStack() as exit_stack:
        service = build_coin_gecko_service(exit_stack=exit_stack)
        resolved = await service.resolve_coin(query=query)
        result = await service.client.list_coin_tickers(
            coin_id=resolved.coin_id, exchanges_ids=exchanges_ids, order=order, page=page, tickers_type=tickers_type
        )
    _print_resolution(resolved=resolved, query=query, as_json=as_json)
    if as_json:
        typer.echo(result.model_dump_json(by_alias=True, indent=2))
    else:
        _render_coin_tickers(result=result)


def ticker_command(
    ticker_id: Annotated[int, typer.Argument(help="Numeric ticker id")],
    total_volume_btc: Annotated[float | None, typer.Option("--total-volume-btc")] = None,
    as_json: JsonOption = False,
) -> None:
    uvloop.run(_ticker(ticker_id=ticker_id, total_volume_btc=total_volume_btc, as_json=as_json))


async def _ticker(*, ticker_id: int, total_volume_btc: float | None, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        client = CoinGeckoApiClient.open(exit_stack=exit_stack)
        price_data = await client.fetch_ticker_price_data(ticker_id=ticker_id, total_volume_btc=total_volume_btc)
    if as_json:
        typer.echo(price_data.model_dump_json(by_alias=True, indent=2))
    else:
        _render_ticker_price_data(price_data=price_data)


def rates_command(
    currency_filter: Annotated[str | None, typer.Argument(help="Only codes or names containing this text")] = None,
    as_json: JsonOption = False,
) -> None:
    uvloop.run(_rates(currency_filter=currency_filter, as_json=as_json))


async def _rates(*, currency_filter: str | None, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        client = CoinGeckoApiClient.open(exit_stack=exit_stack)
        exchange_rates = await client.fetch_exchange_rates()
    if as_json:
        typer.echo(exchange_rates.model_dump_json(by_alias=True, indent=2))
        return
    needle = currency_filter.lower() if currency_filter is not None else None
    rows = [
        [code.upper(), rate.name, rate.unit, f"{rate.value:,.4f}", rate.rate_type]
        for code, rate in sorted(exchange_rates.rates.items(), key=lambda pair: pair[1].value)
        if needle is None or needle in code.lower() or needle in rate.name.lower()
    ]
    print_table(
        title=f"Exchange rates · {len(rows)} of {len(exchange_rates.rates)} · units per 1 BTC",
        columns=["Code", "Name", "Unit", "Value", "Type"],
        rows=rows,
    )


def news_command(
    query: QueryArgument,
    page: Annotated[int, typer.Option("--page", min=1)] = 1,
    per_page: Annotated[int, typer.Option("--per-page", min=1, max=200)] = 10,
    locale: Annotated[str, typer.Option("--locale")] = "en",
    as_json: JsonOption = False,
) -> None:
    uvloop.run(_news(query=query, page=page, per_page=per_page, locale=locale, as_json=as_json))


async def _news(*, query: str, page: int, per_page: int, locale: str, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        service = build_coin_gecko_service(exit_stack=exit_stack)
        resolved = await service.resolve_coin(query=query)
        articles = await service.client.list_coin_news(
            coin_id=resolved.coin_id, page=page, per_page=per_page, locale=locale
        )
    _print_resolution(resolved=resolved, query=query, as_json=as_json)
    if as_json:
        typer.echo(_NEWS_LIST_ADAPTER.dump_json(articles, by_alias=True, indent=2).decode())
    else:
        rows = [
            [
                article.updated_at[:16].replace("T", " "),
                article.news_site,
                article.title if len(article.title) <= 90 else f"{article.title[:87]}...",
            ]
            for article in articles
        ]
        print_table(title=f"News · {resolved.coin_id} · page {page}", columns=["Updated", "Site", "Title"], rows=rows)


def insights_command(
    api_symbol: Annotated[str, typer.Argument(help="api_symbol, for example bitcoin")],
    locale: Annotated[str, typer.Option("--locale")] = "en",
    page: Annotated[int, typer.Option("--page", min=1)] = 1,
    per_page: Annotated[int, typer.Option("--per-page", min=1)] = 10,
    as_json: JsonOption = False,
) -> None:
    uvloop.run(_insights(api_symbol=api_symbol, locale=locale, page=page, per_page=per_page, as_json=as_json))


async def _insights(*, api_symbol: str, locale: str, page: int, per_page: int, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        client = CoinGeckoApiClient.open(exit_stack=exit_stack)
        insights = await client.list_coin_insights(api_symbol=api_symbol, locale=locale, page=page, per_page=per_page)
    if as_json or not insights:
        typer.echo(_INSIGHT_LIST_ADAPTER.dump_json(insights, by_alias=True, indent=2).decode())
    else:
        console.print(f"[bold]{len(insights)} insights[/]")


def categories_command(
    contains: Annotated[
        str | None, typer.Option("--contains", help="Only categories whose id or name contains this text")
    ] = None,
    as_json: JsonOption = False,
) -> None:
    uvloop.run(_categories(contains=contains, as_json=as_json))


async def _categories(*, contains: str | None, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        client = CoinGeckoApiClient.open(exit_stack=exit_stack)
        categories = await client.list_coin_categories()
    if contains is not None:
        needle = contains.lower()
        categories = [
            category for category in categories if needle in category.category_id or needle in category.name.lower()
        ]
    if as_json:
        typer.echo(_CATEGORY_LIST_ADAPTER.dump_json(categories, by_alias=True, indent=2).decode())
        return
    rows = [[category.category_id, category.name] for category in categories[:80]]
    print_table(
        title=f"Categories · {len(categories)} shown",
        columns=["Category id", "Name"],
        rows=rows,
    )


def allocation_command(query: QueryArgument, as_json: JsonOption = False) -> None:
    uvloop.run(_allocation(query=query, as_json=as_json))


async def _allocation(*, query: str, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        service = build_coin_gecko_service(exit_stack=exit_stack)
        resolved = await service.resolve_coin(query=query)
        response = await service.client.fetch_tokenomics_allocation(coin_id=resolved.coin_id)
    _print_resolution(resolved=resolved, query=query, as_json=as_json)
    if as_json:
        typer.echo(response.model_dump_json(by_alias=True, indent=2))
        return
    allocation = response.data
    total_allocated = sum(slice_amount.y for slice_amount in allocation.allocations) or 1.0
    rows = [
        [slice_amount.name, f"{slice_amount.y:,.0f}", f"{slice_amount.y / total_allocated * 100:.2f}%"]
        for slice_amount in allocation.allocations
    ]
    print_line(
        f"[bold]{resolved.coin_id} allocation[/] · supply {format_compact_number(value=allocation.total_supply)} · "
        f"unlocked {format_compact_number(value=allocation.total_unlocked_amount)} · "
        f"locked {format_compact_number(value=allocation.total_locked_amount)} · "
        f"updated {allocation.last_updated_at}"
    )
    print_table(title="Allocations", columns=["Holder", "Amount", "Share"], rows=rows)


def emissions_command(
    query: QueryArgument,
    vs_currency: Annotated[str, typer.Option("--vs")] = "usd",
    as_json: JsonOption = False,
) -> None:
    uvloop.run(_emissions(query=query, vs_currency=vs_currency, as_json=as_json))


async def _emissions(*, query: str, vs_currency: str, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        service = build_coin_gecko_service(exit_stack=exit_stack)
        resolved = await service.resolve_coin(query=query)
        series_list = await service.client.fetch_tokenomics_emissions(coin_id=resolved.coin_id, vs_currency=vs_currency)
    _print_resolution(resolved=resolved, query=query, as_json=as_json)
    if as_json:
        typer.echo(_EMISSIONS_LIST_ADAPTER.dump_json(series_list, by_alias=True, indent=2).decode())
        return
    for series in series_list:
        latest = series.data[-1] if series.data else None
        if latest is None:
            continue
        print_line(
            f"[bold]{series.name}[/] · {len(series.data)} points · latest {format_timestamp_milliseconds(latest.timestamp_unix_milliseconds)}: "
            f"supply {format_compact_number(value=latest.supply_amount)}, "
            f"value {format_money(latest.value_in_currency, currency_code=vs_currency)}"
        )


def financials_command(
    query: QueryArgument,
    duration: Annotated[TokenomicsDuration, typer.Option("--duration")] = TokenomicsDuration.MONTH_1,
    vs_currency: Annotated[str, typer.Option("--vs")] = "usd",
    as_json: JsonOption = False,
) -> None:
    uvloop.run(_financials(query=query, duration=duration, vs_currency=vs_currency, as_json=as_json))


async def _financials(*, query: str, duration: TokenomicsDuration, vs_currency: str, as_json: bool) -> None:
    async with AsyncExitStack() as exit_stack:
        service = build_coin_gecko_service(exit_stack=exit_stack)
        resolved = await service.resolve_coin(query=query)
        series_list = await service.client.fetch_tokenomics_financials(
            coin_id=resolved.coin_id, duration=duration, vs_currency=vs_currency
        )
    _print_resolution(resolved=resolved, query=query, as_json=as_json)
    if as_json:
        typer.echo(_FINANCIALS_LIST_ADAPTER.dump_json(series_list, by_alias=True, indent=2).decode())
        return
    rows = []
    for series in series_list:
        values = [point.value_in_currency for point in series.data]
        latest = values[-1] if values else 0.0
        rows.append(
            [
                series.name,
                str(len(series.data)),
                format_money(latest, currency_code=vs_currency),
                format_money(sum(values), currency_code=vs_currency),
                format_money(sum(values) / len(values) if values else 0.0, currency_code=vs_currency),
            ]
        )
    print_table(
        title=f"{resolved.coin_id} financials · {duration} · in {vs_currency.upper()}",
        columns=["Series", "Points", "Latest", "Total", "Average"],
        rows=rows,
    )


def _print_resolution(*, resolved: ResolvedCoin, query: str, as_json: bool) -> None:
    if as_json or resolved.match_kind not in _RESOLVED_MATCH_KINDS:
        return
    print_line(f"[dim]{query!r} → {resolved.coin_id} ({resolved.name})[/]")


_OHLC_DAYS = (1, 7, 14, 30, 90, 180, 365)


def _parse_ohlc_days(*, raw_days: str) -> int | Literal["max"]:
    if raw_days == "max":
        return "max"
    try:
        parsed = int(raw_days)
    except ValueError:
        parsed = -1
    if parsed not in _OHLC_DAYS:
        comma_days = ", ".join(str(day) for day in _OHLC_DAYS)
        raise typer.BadParameter(f"days must be one of {comma_days} or 'max'")
    return parsed


def _days_label(*, days: str) -> str:
    labels = {"1": "24H", "7": "7D", "14": "14D", "30": "30D", "90": "90D", "180": "180D", "365": "1Y", "max": "MAX"}
    return labels.get(days, days)


def _optional_percentage(value: float | None) -> str:
    if value is None:
        return "-"
    return format_percentage_plain(value)


def _optional_price(value: float | None, *, vs_currency: str) -> str:
    if value is None:
        return "-"
    return format_money(value, currency_code=vs_currency)


def _render_price_summary(*, summary: CoinPriceSummary) -> None:
    currency = summary.vs_currency
    current_price = summary.current_price
    price_text = format_money(current_price, currency_code=currency) if current_price is not None else "-"
    print_line(f"[bold]{summary.name}[/] ({summary.symbol.upper()}) · {summary.coin_id}")
    changes = " · ".join(
        (
            f"1h {_optional_percentage(summary.price_change_percentage_1h)}",
            f"24h {_optional_percentage(summary.price_change_percentage_24h)}",
            f"7d {_optional_percentage(summary.price_change_percentage_7d)}",
        )
    )
    print_line(f"[bold]{price_text}[/] · {changes}")
    detail_bits = []
    if summary.market_cap is not None:
        rank = f" #{summary.market_cap_rank}" if summary.market_cap_rank is not None else ""
        detail_bits.append(f"mcap {format_money(summary.market_cap, currency_code=currency)}{rank}")
    if summary.total_volume is not None:
        detail_bits.append(f"vol {format_money(summary.total_volume, currency_code=currency)}")
    if summary.high_24h is not None and summary.low_24h is not None:
        detail_bits.append(
            f"24h {format_money(summary.low_24h, currency_code=currency)} - {format_money(summary.high_24h, currency_code=currency)}"
        )
    print_line(" · ".join(detail_bits))
    supply_bits = []
    if summary.circulating_supply is not None:
        supply_bits.append(f"circ {format_compact_number(value=summary.circulating_supply)}")
    if summary.max_supply is not None:
        supply_bits.append(f"max {format_compact_number(value=summary.max_supply)}")
    if summary.ath is not None:
        supply_bits.append(f"ATH {format_money(summary.ath, currency_code=currency)}")
    print_line(" · ".join(supply_bits))


def _render_coin_detail(*, detail: MobileCoinDetail) -> None:
    print_line(f"[bold]{detail.name}[/] ({detail.symbol.upper()}) · {detail.id}")
    _render_coin_header(detail=detail)
    if detail.categories:
        print_line(f"[dim]{', '.join(detail.categories)}[/]")
    _render_coin_description(detail=detail)
    market_data = detail.market_data
    if market_data is not None:
        _render_coin_market_block(market_data=market_data)
    _render_coin_sentiment(detail=detail)
    if detail.tickers:
        print_line(f"[dim]{len(detail.tickers)} tickers included; use markets for the table[/]")


def _render_coin_header(*, detail: MobileCoinDetail) -> None:
    header_bits = []
    if detail.market_cap_rank is not None:
        header_bits.append(f"rank #{detail.market_cap_rank}")
    if detail.genesis_date:
        header_bits.append(f"genesis {detail.genesis_date}")
    if detail.hashing_algorithm:
        header_bits.append(detail.hashing_algorithm)
    if detail.watchlist_portfolio_users is not None:
        header_bits.append(f"{detail.watchlist_portfolio_users:,} watchlists")
    print_line(" · ".join(header_bits))


def _render_coin_description(*, detail: MobileCoinDetail) -> None:
    description = detail.description.get("en", "").strip()
    if not description:
        return
    first_paragraph = description.splitlines()[0]
    if len(first_paragraph) > 280:
        first_paragraph = f"{first_paragraph[:277]}..."
    console.print(f"[dim]{first_paragraph}[/]")


def _render_coin_market_block(*, market_data: CoinMarketData) -> None:
    print_line(
        f"Price {format_money(market_data.current_price.get('usd') or 0.0, currency_code='usd')} · "
        f"24h {_optional_percentage(market_data.price_change_percentage_24h)} · "
        f"7d {_optional_percentage(market_data.price_change_percentage_7d)} · "
        f"30d {_optional_percentage(market_data.price_change_percentage_30d)}"
    )
    supply_bits = []
    if market_data.circulating_supply is not None:
        supply_bits.append(f"circ {format_compact_number(value=market_data.circulating_supply)}")
    if market_data.total_supply is not None:
        supply_bits.append(f"total {format_compact_number(value=market_data.total_supply)}")
    if market_data.max_supply is not None:
        supply_bits.append(f"max {format_compact_number(value=market_data.max_supply)}")
    if supply_bits:
        print_line(" · ".join(supply_bits))


def _render_coin_sentiment(*, detail: MobileCoinDetail) -> None:
    sentiment_bits = []
    if detail.sentiment_votes_up_percentage is not None:
        sentiment_bits.append(f"sentiment up {detail.sentiment_votes_up_percentage:.1f}%")
    homepages = [url for url in detail.links.homepage if url]
    if homepages:
        sentiment_bits.append(homepages[0])
    if sentiment_bits:
        print_line(" · ".join(sentiment_bits))


def _render_coin_tickers(*, result: CoinTickers) -> None:
    rows = []
    for ticker in result.tickers[:30]:
        volume_usd = ticker.converted_volume.usd
        spread = f"{ticker.bid_ask_spread_percentage:.3f}%" if ticker.bid_ask_spread_percentage is not None else "-"
        trust = (
            ticker.trust_score
            if ticker.trust_score is not None
            else str(ticker.trust_rank)
            if ticker.trust_rank is not None
            else "-"
        )
        rows.append(
            [
                f"{ticker.base}/{ticker.target}",
                ticker.market.name,
                format_compact_number(value=ticker.last or 0.0),
                format_money(volume_usd or 0.0, currency_code="usd"),
                spread,
                trust,
                "anomaly" if ticker.is_anomaly else ("stale" if ticker.is_stale else ""),
            ]
        )
    print_table(
        title=f"{result.name} markets · {len(result.tickers)} tickers (top 30 shown)",
        columns=["Pair", "Exchange", "Price", "24h volume", "Spread", "Trust", "Flags"],
        rows=rows,
    )


def _render_ticker_price_data(*, price_data: TickerPriceData) -> None:
    centralization = "centralized" if price_data.centralized else "decentralized"
    print_line(f"[bold]{price_data.market_name}[/] · {price_data.market_identifier} · {centralization}")
    print_line(f"last {price_data.last} · volume {price_data.volume} · updated {price_data.last_updated}")
    volume_share = price_data.volume_percentage if price_data.volume_percentage is not None else "-"
    print_line(f"converted last {price_data.converted_last} · volume share {volume_share}%")
