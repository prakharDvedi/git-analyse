import json
import re

from app.agents.llm import call_llm
from app.agents.state import ReviewState
from app.agents.tools import run_tool, tool_registry_description
from app.agents.validation import run_validated_agent_call
from app.core.settings import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are an expert security researcher reviewing code for vulnerabilities.
Be specific. Find REAL issues. Return ONLY JSON."""


SECURITY_PROMPT = """Review this code for security vulnerabilities. Look for:

1. Hardcoded secrets: API keys, tokens, passwords, AWS credentials
2. SQL injection: string concatenation in queries
3. XSS: unsanitized user input in HTML/JS
4. Auth bypass: missing checks, weak validation
5. Command injection: os.system, subprocess with user input
6. Path traversal: unsafe file access

Score against secure engineering fundamentals:
- Input validation and sanitization
- Authentication/authorization boundaries
- Secrets management
- Safe data access patterns

For each file:
{files}

Return JSON format:
{{
  "score": integer 0-100,
  "findings": [
    {{
      "file": "path/to/file",
      "reason": "what is wrong and why it matters",
      "evidence_snippet": "small concrete code snippet or pattern",
      "severity": "low|medium|high|critical",
      "confidence": 0.0
    }}
  ],
  "flagged_files": ["path", ...],
  "recommendations": ["concrete mitigation step", ...]
}}

Be SPECIFIC: "SQL injection in db.py:23" not "SQL injection found"
If no concrete exploit pattern is visible, do not claim one.
Return ONLY valid JSON, no explanation."""

SECURITY_TOOL_SYSTEM_PROMPT = """You are a security investigation agent.
You can inspect the repository using tools before making claims.
Choose the next best tool action to gather evidence.
Return ONLY JSON."""

SECURITY_TOOL_PROMPT = """Investigate this repository for security issues.

Current observations:
{observations}

{tool_registry}

Return JSON:
{{
  "thought": "what you suspect and why",
  "action": {{
    "tool": "list_files|get_file|search_code|finish",
    "args": {{}}
  }}
}}

Rules:
- Use tools to gather evidence before concluding.
- If you have enough evidence, return action.tool = "finish".
- Prefer searching for auth, secret, env, token, password, sql, subprocess, eval, docker, config.
"""


def _extract_json_object(text: str) -> dict | None:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def _run_security_investigation(file_map: dict[str, str]) -> list[str]:
    observations = ["Repository loaded. Start by identifying likely sensitive files."]
    for _ in range(3):
        planner_raw = call_llm(
            prompt=SECURITY_TOOL_PROMPT.format(
                observations="\n".join(f"- {item}" for item in observations),
                tool_registry=tool_registry_description(),
            ),
            system_prompt=SECURITY_TOOL_SYSTEM_PROMPT,
            model=settings.llm_model_security,
            max_tokens=300,
        )
        planner = _extract_json_object(planner_raw)
        if not planner:
            observations.append("Planner output was invalid JSON.")
            continue
        action = planner.get("action", {})
        tool = action.get("tool")
        args = action.get("args", {})
        if tool == "finish":
            break
        if tool not in {"list_files", "get_file", "search_code"}:
            observations.append(f"Unsupported tool requested: {tool}")
            continue
        try:
            result = run_tool(file_map=file_map, tool_name=tool, args=args if isinstance(args, dict) else {})
            observations.append(f"Tool {tool} returned: {result}")
        except Exception as exc:
            observations.append(f"Tool {tool} failed: {str(exc)}")
    return observations


def security_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]
    observations = _run_security_investigation(file_map)
    sample_files = list(file_map.items())[:8]
    files = "\n".join([f"--- {path} ---\n{content[:1500]}" for path, content in sample_files])
    prompt = SECURITY_PROMPT.format(files=files) + "\n\nInvestigation observations:\n" + "\n".join(
        f"- {item}" for item in observations
    )

    try:
        findings = run_validated_agent_call(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            model=settings.llm_model_security,
        )
    except Exception as e:
        findings = {
            "score": 40,
            "findings": [],
            "flagged_files": [],
            "recommendations": [f"Security review failed: {str(e)}"],
        }

    state["security_findings"] = findings
    return state
