from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class CoinLookupSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COINGECKO_LOOKUP_", extra="ignore")

    cache_directory: Path = Path("~/.cache/coingecko-mobile-api").expanduser()
    cache_ttl_seconds: float = 3600.0
    index_size: int = 300
