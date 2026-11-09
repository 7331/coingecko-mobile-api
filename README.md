<img src="assets/icon.svg" width="64" height="64" alt="">

# coingecko-mobile-api

A Python client for the CoinGecko **mobile** API (`mobile-api.coingecko.com`): pydantic models one-to-one with every endpoint, a Typer CLI (`cg`), and a fuzzy coin resolver that turns `BTC`, `bitcvoin` or `Bitcoin` into `bitcoin`.

Built for quick price lookups and as a library for bots (a Discord `.price BTC` command only needs `CoinGeckoService.coin_price_summary`).

## Run

```
cd backend && uv sync
uv run cg btc                      # price for BTC / bitcoin / any fuzzy query
uv run cg eth --vs eur --json
uv run cg chart sol --days 7       # ASCII sparkline
uv run cg markets btc              # top exchanges
uv run cg global                   # total market cap, fear & greed, dominance
uv run cg news btc --per-page 5
uv run cg --help                   # every endpoint command
```

## Layout

- `backend/app/infrastructure/coingecko_api/` — the API client, one method per endpoint, one pydantic model per wire shape, field names kept exactly as the API sends them.
- `backend/app/coingecko/` — the domain: fuzzy coin resolution over a cached top-300 index, the price-summary use case, and the CLI commands.
- `e2e/` — end-to-end flows that drive the built CLI against the live API.

See [ARCHITECTURE.md](ARCHITECTURE.md).
