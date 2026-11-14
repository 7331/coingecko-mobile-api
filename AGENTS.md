# AGENTS.md

Read [`ARCHITECTURE.md`](ARCHITECTURE.md) first. This file lists where this client deliberately
differs from `7331/python-backend-template`.

- The importable package is `coingecko_mobile_api`, not the template's `app`: a library installed
  into another project (skullmasher) cannot own the name `app`. The `cg`/`coingecko` console scripts
  are unchanged.
- This is a **client**, not a service: no FastAPI app, no uvicorn, no Docker, no deploy, no
  Postgres, no passkey accounts, no middlewares, no OpenAPI dump. The process entry points are the
  `cg` / `coingecko` console scripts (`backend/coingecko_mobile_api/cli.py`), which run each command on uvloop.
- The API is the contract. Every method in `coingecko_mobile_api/infrastructure/coingecko_api/client.py` maps to one
  mobile-API endpoint and every model in its `schemas.py` maps to one wire shape with the **exact
  wire field names** (`by_alias=True` round-trips; `rate_type` aliases the wire's `type`). Fields the
  request flags drop (`tickers=false`) are optional and `None`; fields observed `null` on tail coins
  (`CurrencyMap` values) are typed nullable. No invented fields: `/api/v3/coin_insights` returned
  `[]` for every coin and locale tried on 2026-11-09, so `CoinInsight` stays an extra-allow empty
  model until the API ships an item.
- Endpoint behaviour verified live on 2026-11-09, not assumed from the public docs: `coins_lite`
  needs `vs_currency` and `category_id` (422/404 without), `per_page` caps silently at 300, unknown
  `order` values fall back to `market_cap_desc`, `market_chart` needs `days` (422 without) and
  rejects `interval=hourly` beyond 90 days (400), tokenomics `duration` accepts `m1|m3|m6|y1`.
  Ticker `type` accepts `spot` and `perpetuals` on `/api/mobile/coins/{id}/tickers` (verified
  2026-11-14; the v3 `tickers_v2` path 301s to it). The mobile `/api/mobile/search` is not fuzzy (`bitcvoin` →
  `[]`), which is why `coingecko_mobile_api/coingecko/lookup.py` keeps its own on-disk index of the top 300 coins
  (`COINGECKO_LOOKUP_CACHE_*`) and falls back to the search endpoint for coins outside it.
- The ticker `type` and `order` enums in `enums.py` are the closed sets the API rejects on; extend
  them only after a live request proves a new value.
- Verified live on 2026-11-14: the mobile host also serves public v3 paths without a key.
  `/api/v3/coins/markets?ids=` takes several exact coin ids in one call, `/api/v3/rwas/{id}` gives a
  tokenized stock or ETF's name and `asset_type`, and
  `/api/v3/derivatives/exchanges/{id}?include_tickers=unexpired` lists every perpetual pair of a
  venue with CoinGecko's own `coin_id` or `rwa_id`, funding rate, open interest and index basis.
  `/api/v3/coins/top_gainers_losers` is 401 (paid plans only). About 60 requests in two minutes
  from one address starts returning 429.
- `/api/v3/news/{coin_id}` answers with the general feed when a coin has no news of its own, and
  `/api/v3/news` is that general feed with the coins each article is tagged with (20 articles a
  page, `per_page` ignored). `coingecko/news.py` keeps only the articles that are the coin's own: tagged with the coin in the
  feed, or naming the coin (its name, or its symbol of three letters or more in capitals) in the
  title. Comparing the two lists is not enough: the feed is a selection, not every article, and it
  lags the coin endpoint by minutes (measured 2026-11-14). A coin named after a common word still
  collects stray headlines, as CoinGecko's own tags do (`could`, `4`).
  `cg news <coin>` prints those and `cg news-feed` prints the feed.
- A coin's detail arrives with `null` for the price-change maps longer than its age, and with
  `null` links and `country_origin` on tokenized stocks, so those fields are optional; 16 of 19
  young coins and stock tokens failed validation before 2026-11-14.
- The resolver prefers certainty over a guess: an exact id, symbol or name from the search endpoint,
  then an exact id through `coins/markets`, come before prefix and fuzzy hits on the top-300 index.
  Before 2026-11-14 `cg coin tac` returned OriginTrail (TRAC). A failing search request raises
  instead of falling back to a fuzzy guess.
- `requires-python` is `>=3.14`, not the template's `>=3.15`: skullmasher (the Discord bot that
  consumes this library) pins 3.14 in its `.python-version`, so no 3.15-only syntax (PEP 810
  `lazy import`) may enter this package. Verified by running the CLI and the chart renderer on a
  3.14 interpreter.
- Charts are candlesticks from `/api/mobile/coins/{id}/ohlc` (the v3 path 301s to it). Its
  `days` parameter accepts only `1|7|14|30|90|180|365|max` (anything else is a 400) and the candle
  step follows the range: 30 minutes for `1`, 4 hours for `7|14|30`, 4 days for `90|180|365|max`.
  `chart_image.py` renders the PNG on matplotlib; there is no terminal chart.
- Tests are end-to-end runs against the live API (`uv run --project e2e python run_flows.py`); there
  are no unit tests. The flows need network access and cost about 25 requests.
- `scratch/` holds request captures, probes and scratch output; never committed.
