# End-to-end flows of coingecko-mobile-api against the live CoinGecko mobile API

Every flow drives the built CLI (`cg`) as a subprocess with `--json` where machine output matters, or
checks the exit codes of human output. The API is public and rate-limit friendly; the flows make
around 25 requests.

## Run

```
uv sync --project e2e
uv run --project e2e python run_flows.py
```

Requires network access to `mobile-api.coingecko.com`. A failing check raises; the report prints
PASS/FAIL per check and the process exits non-zero when any check fails.

## Flows

- `lookup_flow` — `cg btc`, `cg bitcvoin` (fuzzy), `cg notacoin` (exit 3), `cg price` with `--vs eur`.
- `markets_flow` — `cg coins`, `cg coins --json`, `cg global`, `cg rates eur`.
- `coin_flow` — `cg coin bitcoin --json`, `cg chart`, `cg markets`, `cg news`, `cg allocation`,
  `cg emissions`, `cg financials`, `cg insights`, `cg categories --contains meme`.
- `search_flow` — `cg search bitcoin --json` (typed results for coins, RWAs, NFTs, exchanges,
  categories) and a typo search returning an empty-but-valid payload.
