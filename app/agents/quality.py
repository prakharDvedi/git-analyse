from langfuse import observe

from app.agents.state import ReviewState
from app.agents.validation import run_validated_agent_call
from app.core.langfuse import update_current_span
from app.core.settings import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are a code quality expert analyzing code.
Respond with JSON containing:
- quality_score: integer 0-100
- findings: array of strings (specific issues)
- flagged_files: array of files with issues"""


QUALITY_PROMPT = """Analyze this code for quality issues:

{file_content}

Score against maintainability fundamentals:
- KISS, DRY, clear naming, small focused functions, low nesting, explicitness

Check for:
1. Function complexity (too long, nested)
2. Code duplication
3. Poor naming conventions
4. Missing documentation
5. Magic numbers/strings
6. Error handling issues
7. Readability risks and unclear intent

Respond with JSON:
{{
  "quality_score": 75,
  "findings": [
    {{
      "file": "path/to/file",
      "reason": "specific issue with impact",
      "evidence_snippet": "code evidence",
      "severity": "low|medium|high|critical",
      "confidence": 0.0
    }}
  ],
  "flagged_files": ["file.py"],
  "recommendations": ["specific refactor or cleanup action", "specific refactor or cleanup action"]
}}

Score guidelines:
- 90-100: Excellent, production-ready code
- 70-89: Good, minor improvements possible
- 50-69: Needs refactoring
- 0-49: Significant issues, hard to maintain

Rules:
- Tie findings to concrete files.
- Avoid generic placeholders like "issue 1".

Return ONLY valid JSON."""


@observe(name="quality_agent", as_type="span", capture_input=False, capture_output=False)
def quality_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]

    sample_files = list(file_map.items())[:10]
    file_content = "\n\n".join([f"=== {path} ===\n{content}" for path, content in sample_files])

    try:
        findings = run_validated_agent_call(
            prompt=QUALITY_PROMPT.format(file_content=file_content),
            system_prompt=SYSTEM_PROMPT,
            model=settings.llm_model_quality,
        )
    except Exception as e:
        findings = {
            "score": 40,
            "findings": [],
            "flagged_files": [],
            "recommendations": [f"Quality review failed: {str(e)}"],
        }

    update_current_span(output={"score": findings.get("score", 0), "flagged_files": findings.get("flagged_files", [])})
    return {"quality_findings": findings}
