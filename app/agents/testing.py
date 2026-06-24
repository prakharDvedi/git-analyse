from langfuse import observe

from app.agents.state import ReviewState
from app.agents.validation import run_validated_agent_call
from app.core.langfuse import update_current_span
from app.core.settings import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are a testing expert analyzing code.
Respond with JSON containing:
- score: integer 0-100
- findings: array of strings (specific observations)
- flagged_files: array of test files found"""


TESTING_PROMPT = """Analyze this codebase for testing:

{files}

Score against test strategy fundamentals:
- Unit, integration, and end-to-end coverage signals
- CI enforcement and deterministic test habits

Check for:
1. Test files (test_*.py, *_test.py, spec_*.js, *.test.js)
2. Test directories (__tests__/, tests/, test/)
3. CI/CD configuration (.github/workflows/, .gitlab-ci.yml)
4. Test coverage tools
5. Testing frameworks used
6. Mock/fixture patterns
7. Critical untested risk areas inferred from file structure

Respond with JSON:
{{
  "score": 50,
  "findings": [
    {{
      "file": "path/to/file-or-module",
      "reason": "specific testing gap and impact",
      "evidence_snippet": "test signal or missing pattern evidence",
      "severity": "low|medium|high|critical",
      "confidence": 0.0
    }}
  ],
  "flagged_files": ["test_file.js"],
  "recommendations": ["highest leverage tests to add first", "CI/testing workflow improvement"]
}}

Score guidelines:
- 90-100: Comprehensive tests, good coverage
- 70-89: Some tests present, CI configured
- 50-69: Limited tests, CI missing
- 0-49: No tests found, no CI

Rules:
- Do not output placeholders.
- Prioritize concrete test additions over vague advice.

Return ONLY valid JSON."""


@observe(name="testing_agent", as_type="span", capture_input=False, capture_output=False)
def testing_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]
    files = list(file_map.keys())

    file_list = "\n".join(files)

    try:
        findings = run_validated_agent_call(
            prompt=TESTING_PROMPT.format(files=file_list),
            system_prompt=SYSTEM_PROMPT,
            model=settings.llm_model_testing,
        )
    except Exception as e:
        findings = {
            "score": 40,
            "findings": [],
            "flagged_files": [],
            "recommendations": [f"Testing review failed: {str(e)}"],
        }

    state["testing_findings"] = findings
    update_current_span(output={"score": findings.get("score", 0), "flagged_files": findings.get("flagged_files", [])})
    return state
