from app.agents.state import ReviewState
from app.agents.llm import call_llm

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
    "specific issue with file path and impact",
    "specific issue with file path and impact"
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


def structure_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]
    files = list(file_map.keys())

    file_list = "\n".join(files[:50])

    try:
        result = call_llm(
            STRUCTURE_PROMPT.format(file_list=file_list),
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

    state["structure_findings"] = findings
    return state
