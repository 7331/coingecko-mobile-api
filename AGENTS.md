# AGENTS.md

Read [`ARCHITECTURE.md`](ARCHITECTURE.md) first. This file lists where this client deliberately
differs from `7331/python-backend-template`.

- This is a **client**, not a service: no FastAPI app, no uvicorn, no Docker, no deploy, no
  Postgres, no passkey accounts, no middlewares, no OpenAPI dump. The process entry points are the
  `cg` / `coingecko` console scripts (`backend/app/cli.py`), which run each command on uvloop.
- The API is the contract. Every method in `app/infrastructure/coingecko_api/client.py` maps to one
  mobile-API endpoint and every model in its `schemas.py` maps to one wire shape with the **exact
  wire field names** (`by_alias=True` round-trips; `rate_type` aliases the wire's `type`). Fields the
  request flags drop (`tickers=false`) are optional and `None`; fields observed `null` on tail coins
  (`CurrencyMap` values) are typed nullable. No invented fields: `/api/v3/coin_insights` returned
  `[]` for every coin and locale tried on 2026-11-09, so `CoinInsight` stays an extra-allow empty
  model until the API ships an item.
- Endpoint behaviour verified live on 2026-11-09, not assumed from the public docs: `coins_lite`
  needs `vs_currency` and `category_id` (422/404 without), `per_page` caps silently at 300, unknown
  `order` values fall back to `market_cap_desc`, `market_chart` needs `days` (422 without) and
  rejects `interval=hourly` beyond 90 days (400), ticker `type` only accepts `spot`, tokenomics
  `duration` accepts `m1|m3|m6|y1`. The mobile `/api/mobile/search` is not fuzzy (`bitcvoin` →
  `[]`), which is why `app/coingecko/lookup.py` keeps its own on-disk index of the top 300 coins
  (`COINGECKO_LOOKUP_CACHE_*`) and falls back to the search endpoint for coins outside it.
- The ticker `type` and `order` enums in `enums.py` are the closed sets the API rejects on; extend
  them only after a live request proves a new value.
- Tests are end-to-end runs against the live API (`uv run --project e2e python run_flows.py`); there
  are no unit tests. The flows need network access and cost about 25 requests.
- `scratch/` holds request captures, probes and scratch output; never committed.
