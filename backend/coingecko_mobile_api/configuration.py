from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ApplicationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COINGECKO_", extra="ignore")

    log_level: LogLevel = LogLevel.WARNING


@lru_cache
def read_application_settings() -> ApplicationSettings:
    return ApplicationSettings()
