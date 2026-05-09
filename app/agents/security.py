from app.agents.state import ReviewState
from app.agents.llm import call_llm

SYSTEM_PROMPT = """You are an expert security researcher reviewing code for vulnerabilities.
Be specific. Find REAL issues. Return ONLY JSON."""


SECURITY_PROMPT = """Review this code for security vulnerabilities. Look for:

1. Hardcoded secrets: API keys, tokens, passwords, AWS credentials
2. SQL injection: string concatenation in queries
3. XSS: unsanitized user input in HTML/JS
4. Auth bypass: missing checks, weak validation
5. Command injection: os.system, subprocess with user input
6. Path traversal: unsafe file access

For each file:
{files}

Return JSON format:
{{"score": integer 0-100, "findings": ["specific issue in file:line", ...], "flagged_files": ["path", ...]}}

Be SPECIFIC: "SQL injection in db.py:23" not "SQL injection found"
Return ONLY valid JSON, no explanation."""


def security_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]

    sample_files = list(file_map.items())[:8]
    files = "\n".join([f"--- {path} ---\n{content[:1500]}" for path, content in sample_files])

    try:
        result = call_llm(
            SECURITY_PROMPT.format(files=files),
            system_prompt=SYSTEM_PROMPT
        )

        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            findings = json.loads(json_match.group())
        else:
            findings = {"score": 70, "findings": ["Parse error"], "flagged_files": []}
    except Exception as e:
        findings = {"score": 70, "findings": [f"Error: {str(e)}"], "flagged_files": []}

    state["security_findings"] = findings
    return state