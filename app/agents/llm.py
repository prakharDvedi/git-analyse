import os
from typing import Optional

import requests

from app.core.settings import get_settings

settings = get_settings()

HF_TOKEN = os.getenv("HF_TOKEN") or settings.hf_token


def _resolve_model(model: Optional[str]) -> str:
    return model or settings.llm_model


def _resolve_temperature(temperature: Optional[float]) -> float:
    return settings.llm_temperature if temperature is None else temperature


def _resolve_max_tokens(max_tokens: Optional[int]) -> int:
    return settings.llm_max_tokens if max_tokens is None else max_tokens


def _call_huggingface_chat(
    prompt: str,
    system_prompt: Optional[str],
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        "https://router.huggingface.co/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        raise ValueError("Unexpected Hugging Face router response format")


def _call_ollama_chat(
    prompt: str,
    system_prompt: Optional[str],
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    response = requests.post(
        f"{settings.ollama_base_url}/api/chat",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    message = data.get("message", {})
    return message.get("content", "")


def call_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    resolved_model = _resolve_model(model)
    resolved_temperature = _resolve_temperature(temperature)
    resolved_max_tokens = _resolve_max_tokens(max_tokens)
    provider = settings.llm_provider.lower().strip()

    if provider == "ollama":
        return _call_ollama_chat(
            prompt=prompt,
            system_prompt=system_prompt,
            model=resolved_model,
            temperature=resolved_temperature,
            max_tokens=resolved_max_tokens,
        )
    if provider == "huggingface":
        return _call_huggingface_chat(
            prompt=prompt,
            system_prompt=system_prompt,
            model=resolved_model,
            temperature=resolved_temperature,
            max_tokens=resolved_max_tokens,
        )
    raise ValueError(f"Unsupported llm_provider: {settings.llm_provider}")


def call_llm_json(
    prompt: str,
    system_prompt: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> dict:
    full_prompt = f"""{system_prompt}

Return ONLY valid JSON. No markdown, no explanation.
{prompt}"""

    response_text = call_llm(
        full_prompt,
        system_prompt=None,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    import json
    import re

    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {"error": "Failed to parse JSON", "raw": response_text}
