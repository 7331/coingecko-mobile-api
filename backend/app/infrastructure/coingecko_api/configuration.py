from pydantic_settings import BaseSettings, SettingsConfigDict


class CoinGeckoApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COINGECKO_API_", extra="ignore")

    base_url: str = "https://mobile-api.coingecko.com"
    user_agent: str = "CoinGecko/3.29.1.437 CFNetwork/1331.0.7 Darwin/21.4.0 (iPad iPadOS/15.4)"
    request_timeout_seconds: float = 15.0
    connection_retry_count: int = 2
    failure_attempt_count: int = 3
