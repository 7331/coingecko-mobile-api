from contextlib import AsyncExitStack
from typing import Literal

import httpx
from pydantic import TypeAdapter
import stamina

from app.infrastructure.coingecko_api.configuration import CoinGeckoApiSettings
from app.infrastructure.coingecko_api.enums import (
    CoinsOrder,
    CoinTickersOrder,
    MarketChartInterval,
    TickersType,
    TokenomicsDuration,
)
from app.infrastructure.coingecko_api.errors import (
    CoinGeckoInvalidRequestError,
    CoinGeckoNotFoundError,
    CoinGeckoRateLimitedError,
    CoinGeckoUpstreamError,
)
from app.infrastructure.coingecko_api.schemas import (
    CoinCategory,
    CoinInsight,
    CoinLite,
    CoinTickers,
    ExchangeRates,
    FullCoin,
    GlobalResponse,
    MarketChartSeries,
    MobileCoinDetail,
    MobileSearchResults,
    NewsArticle,
    TickerPriceData,
    TokenomicsAllocationResponse,
    TokenomicsEmissionsSeries,
    TokenomicsFinancialsSeries,
)

_COIN_LITE_LIST_ADAPTER: TypeAdapter[list[CoinLite]] = TypeAdapter(list[CoinLite])
_FULL_COIN_LIST_ADAPTER: TypeAdapter[list[FullCoin]] = TypeAdapter(list[FullCoin])
_INSIGHT_LIST_ADAPTER: TypeAdapter[list[CoinInsight]] = TypeAdapter(list[CoinInsight])
_NEWS_LIST_ADAPTER: TypeAdapter[list[NewsArticle]] = TypeAdapter(list[NewsArticle])
_CATEGORY_LIST_ADAPTER: TypeAdapter[list[CoinCategory]] = TypeAdapter(list[CoinCategory])
_GLOBAL_RESPONSE_ADAPTER: TypeAdapter[GlobalResponse] = TypeAdapter(GlobalResponse)
_SEARCH_RESULTS_ADAPTER: TypeAdapter[MobileSearchResults] = TypeAdapter(MobileSearchResults)
_COIN_DETAIL_ADAPTER: TypeAdapter[MobileCoinDetail] = TypeAdapter(MobileCoinDetail)
_TOKENOMICS_ALLOCATION_ADAPTER: TypeAdapter[TokenomicsAllocationResponse] = TypeAdapter(TokenomicsAllocationResponse)
_TICKER_PRICE_DATA_ADAPTER: TypeAdapter[TickerPriceData] = TypeAdapter(TickerPriceData)
_COIN_TICKERS_ADAPTER: TypeAdapter[CoinTickers] = TypeAdapter(CoinTickers)
_EXCHANGE_RATES_ADAPTER: TypeAdapter[ExchangeRates] = TypeAdapter(ExchangeRates)
_MARKET_CHART_WIRE_ADAPTER: TypeAdapter[dict[str, list[list[float]]]] = TypeAdapter(dict[str, list[list[float]]])
_EMISSIONS_WIRE_ADAPTER: TypeAdapter[list[dict[str, object]]] = TypeAdapter(list[dict[str, object]])
_FINANCIALS_WIRE_ADAPTER: TypeAdapter[list[dict[str, object]]] = TypeAdapter(list[dict[str, object]])


def _flag(*, value: bool) -> str:
    return "true" if value else "false"


def _is_retryable(error: BaseException) -> bool:
    return isinstance(error, httpx.TransportError | CoinGeckoRateLimitedError | CoinGeckoUpstreamError)


class CoinGeckoApiClient:
    def __init__(self, *, settings: CoinGeckoApiSettings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http_client = http_client

    @classmethod
    def open(cls, *, exit_stack: AsyncExitStack, settings: CoinGeckoApiSettings | None = None) -> CoinGeckoApiClient:
        if settings is None:
            settings = CoinGeckoApiSettings()
        http_client = httpx.AsyncClient(
            base_url=settings.base_url,
            headers={"User-Agent": settings.user_agent, "Accept": "application/json"},
            timeout=httpx.Timeout(settings.request_timeout_seconds),
            transport=httpx.AsyncHTTPTransport(retries=settings.connection_retry_count),
            follow_redirects=True,
        )
        exit_stack.push_async_callback(http_client.aclose)
        return cls(settings=settings, http_client=http_client)

    async def list_market_coins(
        self,
        *,
        vs_currency: str,
        category_id: str,
        page: int = 1,
        per_page: int = 50,
        locale: str = "en",
        order: CoinsOrder = CoinsOrder.MARKET_CAP_DESC,
        multiple_currencies: bool = False,
    ) -> list[CoinLite]:
        params = {
            "vs_currency": vs_currency,
            "category_id": category_id,
            "page": str(page),
            "per_page": str(per_page),
            "locale": locale,
            "order": order,
            "multiple_currencies": _flag(value=multiple_currencies),
            "mobile_optimised": "true",
        }
        return await self._request_json("/api/v3/coins_lite", params=params, adapter=_COIN_LITE_LIST_ADAPTER)

    async def list_market_coins_full(
        self,
        *,
        vs_currency: str,
        category_id: str,
        page: int = 1,
        per_page: int = 50,
        locale: str = "en",
        order: CoinsOrder = CoinsOrder.MARKET_CAP_DESC,
        multiple_currencies: bool = False,
    ) -> list[FullCoin]:
        params = {
            "vs_currency": vs_currency,
            "category_id": category_id,
            "page": str(page),
            "per_page": str(per_page),
            "locale": locale,
            "order": order,
            "multiple_currencies": _flag(value=multiple_currencies),
        }
        return await self._request_json("/api/v3/coins_lite", params=params, adapter=_FULL_COIN_LIST_ADAPTER)

    async def fetch_global_market_data(self, *, vs_currency: str | None = None) -> GlobalResponse:
        params: dict[str, str] = {}
        if vs_currency is not None:
            params["vs_currency"] = vs_currency
        return await self._request_json("/api/v3/global", params=params, adapter=_GLOBAL_RESPONSE_ADAPTER)

    async def search(self, *, query: str, vs_currency: str, locale: str = "en") -> MobileSearchResults:
        params = {"query": query, "vs_currency": vs_currency, "locale": locale}
        return await self._request_json("/api/mobile/search", params=params, adapter=_SEARCH_RESULTS_ADAPTER)

    async def fetch_coin(
        self,
        *,
        coin_id: str,
        localization: bool = True,
        tickers: bool = True,
        market_data: bool = True,
        community_data: bool = True,
        developer_data: bool = True,
        sparkline: bool = False,
        include_exchange_logo: bool = True,
        include_categories_details: bool = True,
        include_chain_logo: bool = True,
    ) -> MobileCoinDetail:
        params = {
            "localization": _flag(value=localization),
            "tickers": _flag(value=tickers),
            "market_data": _flag(value=market_data),
            "community_data": _flag(value=community_data),
            "developer_data": _flag(value=developer_data),
            "sparkline": _flag(value=sparkline),
            "include_exchange_logo": _flag(value=include_exchange_logo),
            "include_categories_details": _flag(value=include_categories_details),
            "include_chain_logo": _flag(value=include_chain_logo),
        }
        return await self._request_json(f"/api/mobile/coins/{coin_id}", params=params, adapter=_COIN_DETAIL_ADAPTER)

    async def fetch_market_chart(
        self,
        *,
        coin_id: str,
        vs_currency: str,
        days: int | Literal["max"],
        interval: MarketChartInterval | None = None,
    ) -> MarketChartSeries:
        params: dict[str, str] = {"vs_currency": vs_currency, "days": str(days)}
        if interval is not None:
            params["interval"] = interval
        wire = await self._request_json(
            f"/api/v3/coins/{coin_id}/market_chart", params=params, adapter=_MARKET_CHART_WIRE_ADAPTER
        )
        return MarketChartSeries.model_validate_wire(wire)

    async def fetch_tokenomics_allocation(self, *, coin_id: str) -> TokenomicsAllocationResponse:
        return await self._request_json(
            f"/api/mobile/coins/{coin_id}/tokenomics/allocation", params={}, adapter=_TOKENOMICS_ALLOCATION_ADAPTER
        )

    async def fetch_tokenomics_emissions(self, *, coin_id: str, vs_currency: str) -> list[TokenomicsEmissionsSeries]:
        wire = await self._request_json(
            f"/api/mobile/coins/{coin_id}/tokenomics/emissions",
            params={"vs_currency": vs_currency},
            adapter=_EMISSIONS_WIRE_ADAPTER,
        )
        return [TokenomicsEmissionsSeries.model_validate_wire(series_wire) for series_wire in wire]

    async def fetch_tokenomics_financials(
        self, *, coin_id: str, duration: TokenomicsDuration, vs_currency: str
    ) -> list[TokenomicsFinancialsSeries]:
        wire = await self._request_json(
            f"/api/mobile/coins/{coin_id}/tokenomics/financials",
            params={"duration": duration, "vs_currency": vs_currency},
            adapter=_FINANCIALS_WIRE_ADAPTER,
        )
        return [TokenomicsFinancialsSeries.model_validate_wire(series_wire) for series_wire in wire]

    async def fetch_ticker_price_data(
        self, *, ticker_id: int, total_volume_btc: float | None = None
    ) -> TickerPriceData:
        params: dict[str, str] = {}
        if total_volume_btc is not None:
            params["total_volume_btc"] = str(total_volume_btc)
        return await self._request_json(
            f"/api/v3/tickers/{ticker_id}/price_data", params=params, adapter=_TICKER_PRICE_DATA_ADAPTER
        )

    async def list_coin_tickers(
        self,
        *,
        coin_id: str,
        exchanges_ids: str = "",
        include_exchange_logo: bool = True,
        order: CoinTickersOrder = CoinTickersOrder.TRUST_SCORE_DESC,
        page: int = 1,
        tickers_type: TickersType = TickersType.SPOT,
    ) -> CoinTickers:
        params = {
            "exchanges_ids": exchanges_ids,
            "include_exchange_logo": _flag(value=include_exchange_logo),
            "order": order,
            "page": str(page),
            "type": tickers_type,
        }
        return await self._request_json(
            f"/api/mobile/coins/{coin_id}/tickers", params=params, adapter=_COIN_TICKERS_ADAPTER
        )

    async def fetch_exchange_rates(self) -> ExchangeRates:
        return await self._request_json("/api/v3/exchange_rates", params={}, adapter=_EXCHANGE_RATES_ADAPTER)

    async def list_coin_insights(
        self, *, api_symbol: str, locale: str = "en", page: int = 1, per_page: int = 10
    ) -> list[CoinInsight]:
        params = {"api_symbol": api_symbol, "locale": locale, "page": str(page), "per_page": str(per_page)}
        return await self._request_json("/api/v3/coin_insights", params=params, adapter=_INSIGHT_LIST_ADAPTER)

    async def list_coin_news(
        self, *, coin_id: str, page: int = 1, per_page: int = 10, locale: str = "en"
    ) -> list[NewsArticle]:
        params = {"page": str(page), "per_page": str(per_page), "locale": locale}
        return await self._request_json(f"/api/v3/news/{coin_id}", params=params, adapter=_NEWS_LIST_ADAPTER)

    async def list_coin_categories(self) -> list[CoinCategory]:
        return await self._request_json("/api/v3/coins/categories/list", params={}, adapter=_CATEGORY_LIST_ADAPTER)

    async def _request_json[WireT](self, path: str, *, params: dict[str, str], adapter: TypeAdapter[WireT]) -> WireT:
        async for attempt in stamina.retry_context(
            on=_is_retryable, attempts=self._settings.failure_attempt_count, wait_max=5.0
        ):
            with attempt:
                http_response = await self._http_client.get(path, params=params)
                _raise_for_api_error(http_response)
                return adapter.validate_json(http_response.content)
        raise AssertionError("retry loop returned without a response")


def _raise_for_api_error(http_response: httpx.Response) -> None:
    if http_response.status_code < 400:
        return
    detail = _error_detail(http_response)
    if http_response.status_code == 404:
        raise CoinGeckoNotFoundError(detail)
    if http_response.status_code == 429:
        raise CoinGeckoRateLimitedError(detail)
    if http_response.status_code >= 500:
        raise CoinGeckoUpstreamError(detail)
    raise CoinGeckoInvalidRequestError(detail)


def _error_detail(http_response: httpx.Response) -> str:
    try:
        wire = http_response.json()
    except ValueError:
        return f"HTTP {http_response.status_code}"
    if isinstance(wire, dict):
        for key in ("error", "message"):
            value = wire.get(key)
            if isinstance(value, str):
                return value
    return f"HTTP {http_response.status_code}"
