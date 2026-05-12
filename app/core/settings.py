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
    environment: str = "dev"

    # JWT config
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60

    # DB config
    database_url: str = "sqlite:///./gitanalyse.db"

    # HuggingFace
    hf_token: Optional[str] = None

    # LLM (provider-agnostic defaults)
    llm_provider: str = "ollama"  # ollama | huggingface
    llm_model: str = "qwen2.5-coder:14b"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024

    # Optional per-agent model overrides
    llm_model_structure: Optional[str] = None
    llm_model_security: Optional[str] = None
    llm_model_quality: Optional[str] = None
    llm_model_testing: Optional[str] = None
    llm_model_synthesizer: Optional[str] = None

    # Ollama local endpoint
    ollama_base_url: str = "http://127.0.0.1:11434"

    # GitHub
    github_token: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.environment.lower() != "dev" and settings.jwt_secret == "dev-insecure-change-me":
        raise ValueError("JWT_SECRET must be set in non-dev environments")
    return settings
