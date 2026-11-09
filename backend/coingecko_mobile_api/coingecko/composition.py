from contextlib import AsyncExitStack

from coingecko_mobile_api.coingecko.configuration import CoinLookupSettings
from coingecko_mobile_api.coingecko.lookup import CoinResolver
from coingecko_mobile_api.coingecko.service import CoinGeckoService
from coingecko_mobile_api.infrastructure.coingecko_api.client import CoinGeckoApiClient


def build_coin_gecko_service(*, exit_stack: AsyncExitStack) -> CoinGeckoService:
    client = CoinGeckoApiClient.open(exit_stack=exit_stack)
    resolver = CoinResolver(client=client, settings=CoinLookupSettings())
    return CoinGeckoService(client=client, resolver=resolver)
