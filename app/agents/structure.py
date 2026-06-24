from langfuse import observe

from app.agents.state import ReviewState
from app.agents.validation import run_validated_agent_call
from app.core.langfuse import update_current_span
from app.core.settings import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are a software architecture expert analyzing code.
Respond with JSON containing:
- score: integer 0-100
- findings: array of strings (specific observations)
- flagged_files: array of files with issues"""


STRUCTURE_PROMPT = """Analyze the project structure:

{file_list}

Score against these engineering principles:
- Correctness, Readability, Maintainability, Security by design, Operational simplicity
- Layered architecture (Controller -> Service -> Repository -> Data)
- High cohesion, low coupling

Check for:
1. Folder organization (src/, lib/, app/, services/)
2. Separation of concerns
3. File naming conventions
4. Module organization
5. API/routes pattern
6. Database/access layer separation
7. Signs of tight coupling or cross-layer leakage

Respond with JSON:
{{
  "score": 80,
  "findings": [
    {{
      "file": "path/to/file",
      "reason": "specific issue with impact",
      "evidence_snippet": "file naming/layout evidence",
      "severity": "low|medium|high|critical",
      "confidence": 0.0
    }}
  ],
  "flagged_files": ["path/file.py"],
  "recommendations": [
    "actionable change with expected impact",
    "actionable change with expected impact"
  ]
}}

Score guidelines:
- 90-100: Excellent architecture, clear separation
- 70-89: Good structure, some inconsistencies
- 50-69: Needs organizational improvement
- 0-49: Poor organization, hard to navigate

Rules:
- Every finding must mention a file path when possible.
- Do not invent vulnerabilities or files not present in the input.
- If evidence is weak, state uncertainty explicitly.

Return ONLY valid JSON."""


@observe(name="structure_agent", as_type="span", capture_input=False, capture_output=False)
def structure_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]
    files = list(file_map.keys())

    file_list = "\n".join(files[:50])

    try:
        findings = run_validated_agent_call(
            prompt=STRUCTURE_PROMPT.format(file_list=file_list),
            system_prompt=SYSTEM_PROMPT,
            model="deepseek-ai/DeepSeek-V3-0324:typo",
        )
    except Exception as e:
        findings = {
            "score": 40,
            "findings": [],
            "flagged_files": [],
            "recommendations": [f"Structure review failed: {str(e)}"],
        }

    update_current_span(output={"score": findings.get("score", 0), "flagged_files": findings.get("flagged_files", [])})
    return {"structure_findings": findings}
