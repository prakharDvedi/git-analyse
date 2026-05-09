from app.agents.state import ReviewState
from app.agents.llm import call_llm

SYSTEM_PROMPT = """You are a testing expert analyzing code.
Respond with JSON containing:
- score: integer 0-100
- findings: array of strings (specific observations)
- flagged_files: array of test files found"""


TESTING_PROMPT = """Analyze this codebase for testing:

{files}

Check for:
1. Test files (test_*.py, *_test.py, spec_*.js, *.test.js)
2. Test directories (__tests__/, tests/, test/)
3. CI/CD configuration (.github/workflows/, .gitlab-ci.yml)
4. Test coverage tools
5. Testing frameworks used
6. Mock/fixture patterns

Respond with JSON:
{{
  "score": 50,
  "findings": ["finding 1", "finding 2"],
  "flagged_files": ["test_file.js"]
}}

Score guidelines:
- 90-100: Comprehensive tests, good coverage
- 70-89: Some tests present, CI configured
- 50-69: Limited tests, CI missing
- 0-49: No tests found, no CI

Return ONLY valid JSON."""


def testing_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]
    files = list(file_map.keys())

    file_list = "\n".join(files)

    try:
        result = call_llm(
            TESTING_PROMPT.format(files=file_list),
            system_prompt=SYSTEM_PROMPT
        )

        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            findings = json.loads(json_match.group())
        else:
            findings = {"score": 30, "findings": ["Unable to parse LLM response"], "flagged_files": []}
    except Exception as e:
        findings = {"score": 30, "findings": [f"LLM error: {str(e)}"], "flagged_files": []}

    state["testing_findings"] = findings
    return state