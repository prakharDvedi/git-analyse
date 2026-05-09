from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GitAnalyse"

    # JWT config
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60

    # DB config
    database_url: str = "sqlite:///./gitanalyse.db"

    # HuggingFace
    hf_token: Optional[str] = None

    # GitHub
    github_token: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
