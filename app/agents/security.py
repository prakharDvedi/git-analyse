from app.agents.state import ReviewState
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


def security_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]

    sample_files = list(file_map.items())[:8]
    files = "\n".join([f"--- {path} ---\n{content[:1500]}" for path, content in sample_files])

    try:
        findings = run_validated_agent_call(
            prompt=SECURITY_PROMPT.format(files=files),
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
