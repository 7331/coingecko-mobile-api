from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class MatchKind(StrEnum):
    COIN_ID = "coin_id"
    WEB_SLUG = "web_slug"
    SYMBOL = "symbol"
    NAME = "name"
    PREFIX = "prefix"
    FUZZY = "fuzzy"
    API_SEARCH = "api_search"


class LookupCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    coin_id: str
    symbol: str
    name: str
    market_cap_rank: int | None = None
    similarity: float


class ResolvedCoin(BaseModel):
    model_config = ConfigDict(frozen=True)

    coin_id: str
    web_slug: str
    symbol: str
    name: str
    market_cap_rank: int | None = None
    match_kind: MatchKind
    candidates: tuple[LookupCandidate, ...] = ()


class CoinPriceSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    coin_id: str
    symbol: str
    name: str
    vs_currency: str
    current_price: float | None
    price_change_percentage_1h: float | None = None
    price_change_percentage_24h: float | None = None
    price_change_percentage_7d: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    market_cap: float | None = None
    market_cap_rank: int | None = None
    total_volume: float | None = None
    fully_diluted_valuation: float | None = None
    ath: float | None = None
    ath_change_percentage: float | None = None
    atl: float | None = None
    total_supply: float | None = None
    max_supply: float | None = None
    circulating_supply: float | None = None
    last_updated: str | None = None
