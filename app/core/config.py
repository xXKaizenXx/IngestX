from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRET_DEFAULTS = {
    "whsec_test_change_in_production",
    "dev-stream-token-change-me",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "IngestX"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    database_url: str = "postgresql+psycopg2://ingestx:ingestx@localhost:5432/ingestx"
    redis_url: str = "redis://localhost:6379/0"

    webhook_secret: str = "whsec_test_change_in_production"
    ws_auth_token: str = "dev-stream-token-change-me"

    ingest_rate_limit_per_second: int = 1000
    idempotency_ttl_seconds: int = 86400

    rq_queue_name: str = "webhook_events"
    redis_pubsub_channel: str = "ledger:updates"

    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    api_workers: int = 1
    log_level: str = "INFO"
    run_db_migrations: bool = True

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate_for_runtime(self) -> None:
        if not self.is_production:
            return
        if self.webhook_secret in INSECURE_SECRET_DEFAULTS:
            raise RuntimeError("WEBHOOK_SECRET must be set to a secure value in production")
        if self.ws_auth_token in INSECURE_SECRET_DEFAULTS:
            raise RuntimeError("WS_AUTH_TOKEN must be set to a secure value in production")
        if len(self.webhook_secret) < 24:
            raise RuntimeError("WEBHOOK_SECRET is too short for production")
        if len(self.ws_auth_token) < 24:
            raise RuntimeError("WS_AUTH_TOKEN is too short for production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
