from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized app configuration.

    Loads from environment variables and an optional local `.env` file.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "CodeReviewer"

    # Auth/JWT
    jwt_secret: str = Field(
        "dev-insecure-change-me",
        description="Secret key used to sign JWTs (override via .env in real deployments)",
    )
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60

    # Database
    database_url: str = "sqlite:///./codereviewer.sqlite3"


@lru_cache
def get_settings() -> Settings:
    # Cached so we don't re-parse env repeatedly.
    return Settings()
