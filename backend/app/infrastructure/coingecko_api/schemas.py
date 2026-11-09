from pydantic import BaseModel, ConfigDict, Field, JsonValue

type CurrencyMap = dict[str, float | None]


class Base(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ImageLinks(Base):
    thumb: str
    small: str
    large: str


class CurrencyTriple(Base):
    btc: float | None = None
    eth: float | None = None
    usd: float | None = None


class CoinLiteMarketData(Base):
    current_price: CurrencyMap
    market_cap: CurrencyMap
    total_volume: CurrencyMap
    liquidity: CurrencyMap
    high_24h: CurrencyMap
    low_24h: CurrencyMap
    price_change_24h_in_currency: CurrencyMap
    price_change_percentage_1h_in_currency: CurrencyMap
    price_change_percentage_24h_in_currency: CurrencyMap
    price_change_percentage_7d_in_currency: CurrencyMap
    price_change_percentage_14d_in_currency: CurrencyMap
    price_change_percentage_30d_in_currency: CurrencyMap
    market_cap_change_24h_in_currency: CurrencyMap
    market_cap_change_percentage_24h_in_currency: CurrencyMap
    market_cap_rank: int
    market_cap_rank_with_rehypothecated: int


class CoinLite(Base):
    id: str
    web_slug: str
    symbol: str
    name: str
    image: ImageLinks
    market_data: CoinLiteMarketData
    localization: dict[str, str]


class FullCoin(Base):
    asset_platform_id: str | None = None
    contract_address: str
    description: dict[str, str]
    id: str
    image: ImageLinks
    last_updated: str
    localization: dict[str, str]
    market_data: FullCoinMarketData
    name: str
    public_notice: str | None = None
    symbol: str


class Sparkline(Base):
    price: list[float]


class RoiData(Base):
    times: float
    percentage: float
    currency: str


class CoinMarketData(Base):
    current_price: CurrencyMap
    total_value_locked: float | None = None
    mcap_to_tvl_ratio: float | None = None
    fdv_to_tvl_ratio: float | None = None
    roi: RoiData | None = None
    ath: CurrencyMap
    ath_change_percentage: CurrencyMap
    ath_date: dict[str, str]
    atl: CurrencyMap
    atl_change_percentage: CurrencyMap
    atl_date: dict[str, str]
    market_cap: CurrencyMap
    market_cap_rank: int | None = None
    fully_diluted_valuation: CurrencyMap
    market_cap_fdv_ratio: float | None = None
    total_volume: CurrencyMap
    high_24h: CurrencyMap
    low_24h: CurrencyMap
    price_change_24h: float | None = None
    price_change_percentage_24h: float | None = None
    price_change_percentage_7d: float | None = None
    price_change_percentage_14d: float | None = None
    price_change_percentage_30d: float | None = None
    price_change_percentage_60d: float | None = None
    price_change_percentage_200d: float | None = None
    price_change_percentage_1y: float | None = None
    market_cap_change_24h: float | None = None
    market_cap_change_percentage_24h: float | None = None
    price_change_24h_in_currency: CurrencyMap
    price_change_percentage_1h_in_currency: CurrencyMap
    price_change_percentage_24h_in_currency: CurrencyMap
    price_change_percentage_7d_in_currency: CurrencyMap
    price_change_percentage_14d_in_currency: CurrencyMap
    price_change_percentage_30d_in_currency: CurrencyMap
    price_change_percentage_60d_in_currency: CurrencyMap
    price_change_percentage_200d_in_currency: CurrencyMap
    price_change_percentage_1y_in_currency: CurrencyMap
    market_cap_change_24h_in_currency: CurrencyMap
    market_cap_change_percentage_24h_in_currency: CurrencyMap
    total_supply: float | None = None
    max_supply: float | None = None
    max_supply_infinite: bool | None = None
    circulating_supply: float | None = None
    outstanding_supply: float | None = None
    outstanding_token_value: float | None = None
    last_updated: str | None = None
    sparkline_1h: Sparkline | None = None
    sparkline_7d: Sparkline | None = None


class FullCoinMarketData(Base):
    current_price: CurrencyMap
    roi: RoiData | None = None
    ath: CurrencyMap
    ath_change_percentage: CurrencyMap
    ath_date: dict[str, str]
    atl: CurrencyMap
    atl_change_percentage: CurrencyMap
    atl_date: dict[str, str]
    market_cap: CurrencyMap
    market_cap_rank: int | None = None
    fully_diluted_valuation: CurrencyMap
    total_volume: CurrencyMap
    high_24h: CurrencyMap
    low_24h: CurrencyMap
    price_change_24h_in_currency: CurrencyMap
    price_change_percentage_1h_in_currency: CurrencyMap
    price_change_percentage_24h_in_currency: CurrencyMap
    price_change_percentage_7d_in_currency: CurrencyMap
    price_change_percentage_14d_in_currency: CurrencyMap
    price_change_percentage_30d_in_currency: CurrencyMap
    price_change_percentage_60d_in_currency: CurrencyMap
    price_change_percentage_200d_in_currency: CurrencyMap
    price_change_percentage_1y_in_currency: CurrencyMap
    market_cap_change_24h_in_currency: CurrencyMap
    market_cap_change_percentage_24h_in_currency: CurrencyMap
    total_supply: float | None = None
    circulating_supply: float | None = None
    market_cap_rank_with_rehypothecated: int | None = None


class CoinLinksRepos(Base):
    github: list[str]
    bitbucket: list[str]


class CoinLinks(Base):
    homepage: list[str]
    whitepaper: str | None = None
    blockchain_site: list[str]
    official_forum_url: list[str]
    chat_url: list[str]
    announcement_url: list[str]
    snapshot_url: str | None = None
    twitter_screen_name: str
    facebook_username: str
    bitcointalk_thread_identifier: int | None = None
    telegram_channel_identifier: str
    subreddit_url: str | None = None
    repos_url: CoinLinksRepos


class CommunityData(Base):
    facebook_likes: int | None = None
    reddit_average_posts_48h: float | None = None
    reddit_average_comments_48h: float | None = None
    reddit_subscribers: int | None = None
    reddit_accounts_active_48h: int | None = None
    telegram_channel_user_count: int | None = None


class CodeAdditionsDeletions4Weeks(Base):
    additions: int | None = None
    deletions: int | None = None


class DeveloperData(Base):
    forks: int | None = None
    stars: int | None = None
    subscribers: int | None = None
    total_issues: int | None = None
    closed_issues: int | None = None
    pull_requests_merged: int | None = None
    pull_request_contributors: int | None = None
    code_additions_deletions_4_weeks: CodeAdditionsDeletions4Weeks | None = None
    commit_count_4_weeks: int | None = None
    last_4_weeks_commit_activity_series: list[int] = []


class IcoData(Base):
    ico_start_date: str | None = None
    ico_end_date: str | None = None
    short_desc: str | None = None
    description: str | None = None
    links: dict[str, str] = {}
    softcap_currency: str | None = None
    hardcap_currency: str | None = None
    total_raised_currency: str | None = None
    softcap_amount: float | None = None
    hardcap_amount: float | None = None
    total_raised: float | None = None
    quote_pre_sale_currency: str | None = None
    base_pre_sale_amount: float | None = None
    quote_pre_sale_amount: float | None = None
    quote_public_sale_currency: str | None = None
    base_public_sale_amount: float | None = None
    quote_public_sale_amount: float | None = None
    accepting_currencies: str | None = None
    country_origin: str | None = None
    pre_sale_start_date: str | None = None
    pre_sale_end_date: str | None = None
    whitelist_url: str | None = None
    whitelist_start_date: str | None = None
    whitelist_end_date: str | None = None


class TickerMarket(Base):
    name: str
    identifier: str
    has_trading_incentive: bool | None = None
    logo: str | None = None


class Ticker(Base):
    base: str
    target: str
    market: TickerMarket
    last: float | None = None
    volume: float | None = None
    converted_last: CurrencyTriple
    converted_volume: CurrencyTriple
    trust_score: str | None = None
    bid_ask_spread_percentage: float | None = None
    timestamp: str
    last_traded_at: str
    last_fetch_at: str
    is_anomaly: bool
    is_stale: bool
    trade_url: str | None = None
    token_info_url: str | None = None
    coin_id: str | None = None
    target_coin_id: str | None = None
    coin_mcap_usd: float | None = None
    trust_rank: int | None = None


class CoinCategoryDetail(Base):
    id: str
    name: str


class DetailPlatform(Base):
    decimal_place: int | None = None
    contract_address: str | None = None
    logo: str | None = None


class MobileCoinDetail(Base):
    id: str
    symbol: str
    name: str
    web_slug: str
    asset_platform_id: str | None = None
    platforms: dict[str, str]
    detail_platforms: dict[str, DetailPlatform]
    block_time_in_minutes: int | None = None
    hashing_algorithm: str | None = None
    categories: list[str]
    categories_details: list[CoinCategoryDetail] | None = None
    preview_listing: bool
    public_notice: str | None = None
    additional_notices: list[str]
    localization: dict[str, str] | None = None
    description: dict[str, str]
    links: CoinLinks
    image: ImageLinks
    country_origin: str
    genesis_date: str | None = None
    listing_price: float | None = None
    listing_currency: str | None = None
    listing_timestamp: str | None = None
    listing_source: str | None = None
    listing_source_url: str | None = None
    has_supply_breakdown: bool
    sentiment_votes_up_percentage: float | None = None
    sentiment_votes_down_percentage: float | None = None
    watchlist_portfolio_users: int | None = None
    market_cap_rank: int | None = None
    market_data: CoinMarketData | None = None
    community_data: CommunityData | None = None
    developer_data: DeveloperData | None = None
    ico_data: IcoData | None = None
    status_updates: list[JsonValue]
    last_updated: str | None = None
    tickers: list[Ticker] | None = None
    rwas: list[JsonValue]
    total_treasury_holdings: float | None = None


class FearAndGreedIndex(Base):
    value: int
    sentiment: str


class GlobalMarketData(Base):
    active_cryptocurrencies: int
    upcoming_icos: int
    ongoing_icos: int
    ended_icos: int
    markets: int
    total_market_cap: CurrencyMap
    total_volume: CurrencyMap
    market_cap_percentage: CurrencyMap
    market_cap_change_percentage_24h_usd: float
    volume_change_percentage_24h_usd: float
    fear_and_greed_index: FearAndGreedIndex
    updated_at: int


class GlobalResponse(Base):
    data: GlobalMarketData


class SearchCoinData(Base):
    price: float | None = None
    price_btc: float | None = None
    price_change_percentage_24h: float | None = None
    coin_id: int | None = None


class SearchCoin(Base):
    thumb: str
    name: str
    symbol: str
    market_cap_rank: int | None = None
    id: str
    data: SearchCoinData


class SearchRwaData(Base):
    benchmark_price: float | None = None
    spot_price: float | None = None
    price_change_percentage_24h: float | None = None


class SearchRwa(Base):
    thumb: str
    name: str
    symbol: str
    market_cap_rank: int | None = None
    id: str
    data: SearchRwaData


class NftContractSearchData(Base):
    native_currency_symbol: str | None = None
    floor_price_in_native_currency: str | None = None
    floor_price_24h_percentage_change: str | None = None


class NftContractSearchResult(Base):
    thumb: str
    name: str
    symbol: str
    id: str
    data: NftContractSearchData


class SearchMarket(Base):
    thumb: str
    name: str
    id: str
    market_type: str


class SearchCategory(Base):
    name: str
    id: int
    slug: str
    top_3_coins_images: list[str]


class MobileSearchResults(Base):
    coins: list[SearchCoin]
    rwas: list[SearchRwa]
    nft_contracts: list[NftContractSearchResult] = Field(alias="nftContracts")
    markets: list[SearchMarket]
    categories: list[SearchCategory]


class ChartPoint(Base):
    timestamp_unix_milliseconds: int
    value: float

    @classmethod
    def from_wire_pair(cls, wire_pair: list[float]) -> ChartPoint:
        timestamp_milliseconds, value = wire_pair
        return cls(timestamp_unix_milliseconds=round(timestamp_milliseconds), value=value)


class MarketChartSeries(Base):
    prices: list[ChartPoint]
    market_caps: list[ChartPoint]
    total_volumes: list[ChartPoint]

    @classmethod
    def model_validate_wire(cls, wire: dict[str, list[list[float]]]) -> MarketChartSeries:
        return cls(
            prices=[ChartPoint.from_wire_pair(wire_pair) for wire_pair in wire["prices"]],
            market_caps=[ChartPoint.from_wire_pair(wire_pair) for wire_pair in wire["market_caps"]],
            total_volumes=[ChartPoint.from_wire_pair(wire_pair) for wire_pair in wire["total_volumes"]],
        )


class TokenomicsSlice(Base):
    name: str
    y: float


class TokenomicsAllocation(Base):
    total_supply: float
    total_unlocked_amount: float
    total_locked_amount: float
    total_tbd_locked_amount: float
    last_updated_at: str
    allocations: list[TokenomicsSlice]


class TokenomicsAllocationResponse(Base):
    id: str
    data: TokenomicsAllocation


class EmissionsPoint(Base):
    timestamp_unix_milliseconds: int
    supply_amount: float
    value_in_currency: float

    @classmethod
    def from_wire_triple(cls, wire_triple: list[float]) -> EmissionsPoint:
        timestamp_milliseconds, supply_amount, value_in_currency = wire_triple
        return cls(
            timestamp_unix_milliseconds=round(timestamp_milliseconds),
            supply_amount=supply_amount,
            value_in_currency=value_in_currency,
        )


class TokenomicsEmissionsSeries(Base):
    name: str
    data: list[EmissionsPoint]

    @classmethod
    def model_validate_wire(cls, wire: dict[str, object]) -> TokenomicsEmissionsSeries:
        name = wire["name"]
        raw_data = wire["data"]
        if not isinstance(name, str) or not isinstance(raw_data, list):
            raise TypeError("tokenomics emissions series expects name and data")
        return cls(name=name, data=[EmissionsPoint.from_wire_triple(wire_triple) for wire_triple in raw_data])


class FinancialsPoint(Base):
    timestamp_unix_milliseconds: int
    value_in_currency: float

    @classmethod
    def from_wire_pair(cls, wire_pair: list[float]) -> FinancialsPoint:
        timestamp_milliseconds, value_in_currency = wire_pair
        return cls(timestamp_unix_milliseconds=round(timestamp_milliseconds), value_in_currency=value_in_currency)


class TokenomicsFinancialsSeries(Base):
    name: str
    data: list[FinancialsPoint]

    @classmethod
    def model_validate_wire(cls, wire: dict[str, object]) -> TokenomicsFinancialsSeries:
        name = wire["name"]
        raw_data = wire["data"]
        if not isinstance(name, str) or not isinstance(raw_data, list):
            raise TypeError("tokenomics financials series expects name and data")
        return cls(name=name, data=[FinancialsPoint.from_wire_pair(wire_pair) for wire_pair in raw_data])


class TickerPriceData(Base):
    id: int
    converted_last: dict[str, str]
    bid_ask_spread: float | None = None
    upper_depth: float | None = None
    lower_depth: float | None = None
    converted_volume: dict[str, str]
    volume_percentage: float | None = None
    timestamp: str
    last_updated: str
    trust_score: str | None = None
    market_name: str
    last: str
    volume: str
    market_identifier: str
    centralized: bool


class CoinTickers(Base):
    name: str
    tickers: list[Ticker]


class ExchangeRate(Base):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    unit: str
    value: float
    rate_type: str = Field(alias="type")


class ExchangeRates(Base):
    rates: dict[str, ExchangeRate]


class CoinInsight(Base):
    model_config = ConfigDict(extra="allow")


class NewsArticle(Base):
    title: str
    authors: str
    thumb_1x: str
    thumb_2x: str
    news_site: str
    url: str
    updated_at: str
    crawled_at: str


class CoinCategory(Base):
    category_id: str
    name: str
