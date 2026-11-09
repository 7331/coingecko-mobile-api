from contextlib import AsyncExitStack

from app.coingecko.configuration import CoinLookupSettings
from app.coingecko.lookup import CoinResolver
from app.coingecko.service import CoinGeckoService
from app.infrastructure.coingecko_api.client import CoinGeckoApiClient


def build_coin_gecko_service(*, exit_stack: AsyncExitStack) -> CoinGeckoService:
    client = CoinGeckoApiClient.open(exit_stack=exit_stack)
    resolver = CoinResolver(client=client, settings=CoinLookupSettings())
    return CoinGeckoService(client=client, resolver=resolver)
