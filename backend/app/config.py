from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    modelflow_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./model_flow.db"
    registry_lease_seconds: int = Field(default=30, gt=0)
    registry_heartbeat_seconds: int = Field(default=10, gt=0)
    executor_max_concurrency: int = Field(default=8, gt=0)
    event_retention_hours: int = Field(default=168, gt=0)
    brain_api_base_url: str | None = None
    brain_api_key: str | None = None
    worker_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
