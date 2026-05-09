import os
from typing import Optional

from huggingface_hub import InferenceClient

from app.core.settings import get_settings

settings = get_settings()

HF_TOKEN = os.getenv("HF_TOKEN") or settings.hf_token

DEFAULT_MODEL = "meta-llama/Llama-3.2-1B-Instruct"


def get_client() -> InferenceClient:
    return InferenceClient(model=DEFAULT_MODEL, token=HF_TOKEN)


def call_llm(prompt: str, system_prompt: Optional[str] = None) -> str:
    client = get_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat_completion(messages, max_tokens=1024)
    return response.choices[0].message.content


def call_llm_json(prompt: str, system_prompt: str) -> dict:
    client = get_client()

    full_prompt = f"""{system_prompt}

Return ONLY valid JSON. No markdown, no explanation.
{prompt}"""

    response = client.text_generation(full_prompt, max_new_tokens=1024)

    import json
    import re

    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {"error": "Failed to parse JSON", "raw": response}