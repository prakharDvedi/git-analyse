from functools import lru_cache
from typing import Any

from langfuse import Langfuse

from app.core.settings import get_settings


@lru_cache
def get_langfuse_client() -> Langfuse | None:
    settings = get_settings()
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
        environment=settings.environment,
    )


def update_current_span(**kwargs: Any) -> None:
    client = get_langfuse_client()
    if client is not None:
        client.update_current_span(**kwargs)


def set_current_trace_io(*, input: Any = None, output: Any = None) -> None:
    client = get_langfuse_client()
    if client is not None:
        client.set_current_trace_io(input=input, output=output)


def flush_langfuse() -> None:
    client = get_langfuse_client()
    if client is not None:
        client.flush()
