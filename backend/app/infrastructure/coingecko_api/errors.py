class CoinGeckoApiError(Exception):
    pass


class CoinGeckoNotFoundError(CoinGeckoApiError):
    pass


class CoinGeckoInvalidRequestError(CoinGeckoApiError):
    pass


class CoinGeckoRateLimitedError(CoinGeckoApiError):
    pass


class CoinGeckoUpstreamError(CoinGeckoApiError):
    pass
