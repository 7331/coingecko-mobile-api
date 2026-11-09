from app.coingecko.errors import CoinNotFoundError
from app.coingecko.lookup import CoinResolver
from app.coingecko.types import CoinPriceSummary, ResolvedCoin
from app.infrastructure.coingecko_api.client import CoinGeckoApiClient
from app.infrastructure.coingecko_api.errors import CoinGeckoInvalidRequestError


class CoinGeckoService:
    def __init__(self, *, client: CoinGeckoApiClient, resolver: CoinResolver) -> None:
        self.client = client
        self.resolver = resolver

    async def resolve_coin(self, *, query: str) -> ResolvedCoin:
        return await self.resolver.resolve_coin(query=query)

    async def coin_price_summary(self, *, query: str, vs_currency: str = "usd") -> CoinPriceSummary:
        resolved = await self.resolve_coin(query=query)
        detail = await self.client.fetch_coin(
            coin_id=resolved.coin_id,
            localization=False,
            tickers=False,
            market_data=True,
            community_data=False,
            developer_data=False,
            sparkline=False,
            include_exchange_logo=False,
            include_categories_details=False,
            include_chain_logo=False,
        )
        market_data = detail.market_data
        if market_data is None:
            raise CoinGeckoInvalidRequestError(f"coin {resolved.coin_id} returned no market data")
        currency = vs_currency.lower()
        if currency not in market_data.current_price:
            raise CoinNotFoundError(query=f"{resolved.coin_id} in {vs_currency}")
        return CoinPriceSummary(
            coin_id=resolved.coin_id,
            symbol=resolved.symbol,
            name=resolved.name,
            vs_currency=currency,
            current_price=market_data.current_price.get(currency),
            price_change_percentage_1h=market_data.price_change_percentage_1h_in_currency.get(currency),
            price_change_percentage_24h=market_data.price_change_percentage_24h_in_currency.get(currency),
            price_change_percentage_7d=market_data.price_change_percentage_7d_in_currency.get(currency),
            high_24h=market_data.high_24h.get(currency),
            low_24h=market_data.low_24h.get(currency),
            market_cap=market_data.market_cap.get(currency),
            market_cap_rank=market_data.market_cap_rank,
            total_volume=market_data.total_volume.get(currency),
            fully_diluted_valuation=market_data.fully_diluted_valuation.get(currency),
            ath=market_data.ath.get(currency),
            ath_change_percentage=market_data.ath_change_percentage.get(currency),
            atl=market_data.atl.get(currency),
            total_supply=market_data.total_supply,
            max_supply=market_data.max_supply,
            circulating_supply=market_data.circulating_supply,
            last_updated=market_data.last_updated,
        )
