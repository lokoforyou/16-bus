from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "16 Bus Backend"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api"
    booking_hold_minutes: int = 5

    database_url: str = Field(
        default="sqlite:///./16_bus.db",
        validation_alias="16_BUS_SUPABASE_URL",
    )
    redis_dsn: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expiry_minutes: int = 30

    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
