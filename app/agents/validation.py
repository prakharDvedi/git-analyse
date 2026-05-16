import json
import re
from typing import Optional

from pydantic import ValidationError

from app.agents.llm import call_llm
from app.agents.schemas import AgentOutput


REPAIR_SUFFIX = """

Your previous output was invalid for the required schema.
Fix it now and return ONLY valid JSON.
Do not use placeholder items.
Every finding must include: file, reason, evidence_snippet, severity (low|medium|high|critical), confidence (0..1).
"""


def _extract_json_object(text: str) -> Optional[dict]:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def run_validated_agent_call(
    prompt: str,
    system_prompt: str,
    model: Optional[str],
    max_retries: int = 2,
) -> dict:
    attempt_prompt = prompt
    for _ in range(max_retries + 1):
        raw = call_llm(
            prompt=attempt_prompt,
            system_prompt=system_prompt,
            model=model,
        )
        data = _extract_json_object(raw)
        if data is None:
            attempt_prompt = prompt + REPAIR_SUFFIX
            continue
        try:
            parsed = AgentOutput.model_validate(data)
            return parsed.model_dump()
        except ValidationError:
            attempt_prompt = prompt + REPAIR_SUFFIX
            continue

    # Deterministic fallback to keep pipeline stable.
    return AgentOutput(
        score=40,
        findings=[],
        flagged_files=[],
        recommendations=["Review failed due to invalid LLM output; rerun with stronger model/context."],
    ).model_dump()

