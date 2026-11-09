from app.coingecko.types import LookupCandidate


class CoinNotFoundError(Exception):
    def __init__(self, *, query: str, candidates: tuple[LookupCandidate, ...] = ()) -> None:
        self.query = query
        self.candidates = candidates
        message = f"no coin matches {query!r}"
        if candidates:
            best = candidates[0]
            message += f"; closest: {best.name} ({best.symbol})"
        super().__init__(message)
