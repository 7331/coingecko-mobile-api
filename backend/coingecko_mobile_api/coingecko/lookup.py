from difflib import SequenceMatcher
from pathlib import Path
import time

import httpx
from pydantic import BaseModel, ValidationError

from coingecko_mobile_api.coingecko.configuration import CoinLookupSettings
from coingecko_mobile_api.coingecko.errors import CoinNotFoundError
from coingecko_mobile_api.coingecko.types import LookupCandidate, MatchKind, ResolvedCoin
from coingecko_mobile_api.infrastructure.coingecko_api.client import CoinGeckoApiClient
from coingecko_mobile_api.infrastructure.coingecko_api.enums import CoinsOrder
from coingecko_mobile_api.infrastructure.coingecko_api.errors import CoinGeckoApiError
from coingecko_mobile_api.infrastructure.coingecko_api.schemas import CoinLite
from coingecko_mobile_api.shared.logging import get_logger

logger = get_logger(__name__)

_FUZZY_SIMILARITY_CUTOFF = 0.72
_CANDIDATE_COUNT = 5


class CoinIndex(BaseModel):
    fetched_at_unix_seconds: float
    coins: list[CoinLite]

    def by_id(self) -> dict[str, CoinLite]:
        return {coin.id: coin for coin in self.coins}

    def by_web_slug(self) -> dict[str, CoinLite]:
        return {coin.web_slug: coin for coin in self.coins}

    def by_symbol(self) -> dict[str, CoinLite]:
        best: dict[str, CoinLite] = {}
        for coin in self.coins:
            current = best.get(coin.symbol)
            if current is None or _rank(coin) < _rank(current):
                best[coin.symbol] = coin
        return best

    def by_name(self) -> dict[str, CoinLite]:
        best: dict[str, CoinLite] = {}
        for coin in self.coins:
            name_key = coin.name.lower()
            current = best.get(name_key)
            if current is None or _rank(coin) < _rank(current):
                best[name_key] = coin
        return best


def _rank(coin: CoinLite) -> int:
    return coin.market_data.market_cap_rank


class CoinResolver:
    def __init__(self, *, client: CoinGeckoApiClient, settings: CoinLookupSettings) -> None:
        self._client = client
        self._settings = settings

    async def resolve_coin(self, *, query: str) -> ResolvedCoin:
        normalized = query.strip().lower()
        if not normalized:
            raise CoinNotFoundError(query=query)
        index = await self._read_or_refresh_index()
        exact = _find_exact(index=index, normalized=normalized)
        if exact is not None:
            return exact
        prefix = _find_prefix(index=index, normalized=normalized)
        if prefix is not None:
            return prefix
        fuzzy_candidates = _fuzzy_candidates(index=index, normalized=normalized)
        if fuzzy_candidates and fuzzy_candidates[0].similarity >= _FUZZY_SIMILARITY_CUTOFF:
            best = fuzzy_candidates[0]
            resolved_from_index = index.by_id().get(best.coin_id)
            if resolved_from_index is not None:
                return _resolved(coin=resolved_from_index, match_kind=MatchKind.FUZZY, candidates=fuzzy_candidates)
        api_candidates = await self._api_search_candidates(query=query)
        if api_candidates:
            best = api_candidates[0]
            return ResolvedCoin(
                coin_id=best.coin_id,
                web_slug=best.coin_id,
                symbol=best.symbol,
                name=best.name,
                market_cap_rank=best.market_cap_rank,
                match_kind=MatchKind.API_SEARCH,
                candidates=api_candidates,
            )
        raise CoinNotFoundError(query=query, candidates=fuzzy_candidates)

    async def _read_or_refresh_index(self) -> CoinIndex:
        cached = self._read_index_file()
        if cached is not None and not self._is_stale(cached):
            return cached
        try:
            coins = await self._client.list_market_coins(
                vs_currency="usd",
                category_id="300",
                per_page=self._settings.index_size,
                order=CoinsOrder.MARKET_CAP_DESC,
            )
        except (CoinGeckoApiError, httpx.HTTPError, ValidationError) as fetch_error:
            if cached is not None:
                logger.warning("Coin index refresh failed; serving stale cache", error=str(fetch_error))
                return cached
            raise
        index = CoinIndex(fetched_at_unix_seconds=time.time(), coins=coins)
        self._write_index_file(index)
        return index

    def _read_index_file(self) -> CoinIndex | None:
        index_path = self._index_path()
        try:
            raw = index_path.read_bytes()
        except OSError:
            return None
        try:
            return CoinIndex.model_validate_json(raw)
        except ValidationError:
            return None

    def _write_index_file(self, index: CoinIndex) -> None:
        index_path = self._index_path()
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(index.model_dump_json())

    def _index_path(self) -> Path:
        return self._settings.cache_directory / "coin_index.json"

    def _is_stale(self, index: CoinIndex) -> bool:
        age_seconds = time.time() - index.fetched_at_unix_seconds
        return age_seconds > self._settings.cache_ttl_seconds

    async def _api_search_candidates(self, *, query: str) -> tuple[LookupCandidate, ...]:
        try:
            results = await self._client.search(query=query, vs_currency="usd")
        except CoinGeckoApiError, httpx.HTTPError:
            return ()
        return tuple(
            LookupCandidate(
                coin_id=coin.id,
                symbol=coin.symbol,
                name=coin.name,
                market_cap_rank=coin.market_cap_rank,
                similarity=SequenceMatcher(None, query.strip().lower(), coin.name.lower()).ratio(),
            )
            for coin in results.coins[:_CANDIDATE_COUNT]
        )


def _find_exact(*, index: CoinIndex, normalized: str) -> ResolvedCoin | None:
    lookups = (
        (MatchKind.COIN_ID, index.by_id()),
        (MatchKind.WEB_SLUG, index.by_web_slug()),
        (MatchKind.SYMBOL, index.by_symbol()),
        (MatchKind.NAME, index.by_name()),
    )
    for match_kind, lookup in lookups:
        coin = lookup.get(normalized)
        if coin is not None:
            return _resolved(coin=coin, match_kind=match_kind, candidates=())
    return None


def _find_prefix(*, index: CoinIndex, normalized: str) -> ResolvedCoin | None:
    matches = [
        coin for coin in index.coins if coin.symbol.startswith(normalized) or coin.name.lower().startswith(normalized)
    ]
    if not matches:
        return None
    matches.sort(key=_rank)
    return _resolved(coin=matches[0], match_kind=MatchKind.PREFIX, candidates=_candidates(matches))


def _fuzzy_candidates(*, index: CoinIndex, normalized: str) -> tuple[LookupCandidate, ...]:
    scored = []
    for coin in index.coins:
        symbol_similarity = SequenceMatcher(None, normalized, coin.symbol).ratio()
        name_similarity = SequenceMatcher(None, normalized, coin.name.lower()).ratio()
        similarity = max(symbol_similarity, name_similarity)
        scored.append((similarity, coin))
    scored.sort(key=lambda pair: (-pair[0], _rank(pair[1])))
    return tuple(
        LookupCandidate(
            coin_id=coin.id,
            symbol=coin.symbol,
            name=coin.name,
            market_cap_rank=coin.market_data.market_cap_rank,
            similarity=round(similarity, 4),
        )
        for similarity, coin in scored[:_CANDIDATE_COUNT]
        if similarity >= _FUZZY_SIMILARITY_CUTOFF
    )


def _candidates(coins: list[CoinLite]) -> tuple[LookupCandidate, ...]:
    return tuple(
        LookupCandidate(
            coin_id=coin.id,
            symbol=coin.symbol,
            name=coin.name,
            market_cap_rank=coin.market_data.market_cap_rank,
            similarity=1.0,
        )
        for coin in coins[:_CANDIDATE_COUNT]
    )


def _resolved(*, coin: CoinLite, match_kind: MatchKind, candidates: tuple[LookupCandidate, ...]) -> ResolvedCoin:
    return ResolvedCoin(
        coin_id=coin.id,
        web_slug=coin.web_slug,
        symbol=coin.symbol,
        name=coin.name,
        market_cap_rank=coin.market_data.market_cap_rank,
        match_kind=match_kind,
        candidates=candidates,
    )
