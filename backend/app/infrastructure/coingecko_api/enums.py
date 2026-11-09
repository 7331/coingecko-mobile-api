from enum import StrEnum


class CoinsOrder(StrEnum):
    MARKET_CAP_DESC = "market_cap_desc"
    MARKET_CAP_ASC = "market_cap_asc"
    H24_CHANGE_DESC = "h24_change_desc"
    H24_CHANGE_ASC = "h24_change_asc"
    VOLUME_DESC = "volume_desc"
    RECENTLY_ADDED_DESC = "recently_added_desc"


class CoinTickersOrder(StrEnum):
    TRUST_SCORE_DESC = "trust_score_desc"
    TRUST_SCORE_ASC = "trust_score_asc"
    VOLUME_DESC = "volume_desc"
    VOLUME_ASC = "volume_asc"


class TickersType(StrEnum):
    SPOT = "spot"


class TokenomicsDuration(StrEnum):
    MONTH_1 = "m1"
    MONTH_3 = "m3"
    MONTH_6 = "m6"
    YEAR_1 = "y1"


class MarketChartInterval(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"
