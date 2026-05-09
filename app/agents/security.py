from app.agents.state import ReviewState
from app.agents.llm import call_llm

SYSTEM_PROMPT = """You are a security expert analyzing code.
Respond with JSON containing:
- score: integer 0-100
- findings: array of strings (specific issues found)
- flagged_files: array of file paths with issues"""


SECURITY_PROMPT = """Analyze this code for security vulnerabilities:

{file_content}

For each file, check for:
1. Hardcoded secrets, API keys, tokens, passwords
2. SQL injection vulnerabilities
3. XSS vulnerabilities
4. Authentication issues
5. Unsafe inputs
6. Exposed credentials

Respond with JSON:
{{
  "score": 75,
  "findings": ["issue 1", "issue 2"],
  "flagged_files": ["file.py", "auth.js"]
}}

Score guidelines:
- 90-100: No issues found
- 70-89: Minor issues, best practices not followed
- 50-69: Moderate security concerns
- 0-49: Critical vulnerabilities present

Return ONLY valid JSON."""


def security_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]

    sample_files = list(file_map.items())[:10]
    file_content = "\n\n".join([f"=== {path} ===\n{content}" for path, content in sample_files])

    try:
        result = call_llm(
            SECURITY_PROMPT.format(file_content=file_content),
            system_prompt=SYSTEM_PROMPT
        )

        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            findings = json.loads(json_match.group())
        else:
            findings = {"score": 70, "findings": ["Unable to parse LLM response"], "flagged_files": []}
    except Exception as e:
        findings = {"score": 70, "findings": [f"LLM error: {str(e)}"], "flagged_files": []}

    state["security_findings"] = findings
    return state