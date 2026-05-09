from app.agents.state import ReviewState
from app.agents.llm import call_llm

SYSTEM_PROMPT = """You are a code quality expert analyzing code.
Respond with JSON containing:
- score: integer 0-100
- findings: array of strings (specific issues)
- flagged_files: array of files with issues"""


QUALITY_PROMPT = """Analyze this code for quality issues:

{file_content}

Check for:
1. Function complexity (too long, nested)
2. Code duplication
3. Poor naming conventions
4. Missing documentation
5. Magic numbers/strings
6. Error handling issues

Respond with JSON:
{{
  "score": 75,
  "findings": ["issue 1", "issue 2"],
  "flagged_files": ["file.py"]
}}

Score guidelines:
- 90-100: Excellent, production-ready code
- 70-89: Good, minor improvements possible
- 50-69: Needs refactoring
- 0-49: Significant issues, hard to maintain

Return ONLY valid JSON."""


def quality_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]

    sample_files = list(file_map.items())[:10]
    file_content = "\n\n".join([f"=== {path} ===\n{content}" for path, content in sample_files])

    try:
        result = call_llm(
            QUALITY_PROMPT.format(file_content=file_content),
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

    state["quality_findings"] = findings
    return state