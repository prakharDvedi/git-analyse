from __future__ import annotations

from langfuse import observe

from app.agents.llm import call_llm_json
from app.agents.state import ReviewState
from app.core.langfuse import update_current_span
from app.core.settings import get_settings

settings = get_settings()

SYNTH_SYSTEM_PROMPT = """You are a principal engineer producing a final code-review verdict.
You receive dimension-level findings from specialized agents.
Produce a grounded, specific, non-generic report.
Do not invent files or vulnerabilities not present in inputs."""


@observe(name="synthesizer", as_type="span", capture_input=False, capture_output=False)
def synthesizer_node(state: ReviewState) -> ReviewState:
    structure = state.get("structure_findings", {})
    security = state.get("security_findings", {})
    quality = state.get("quality_findings", {})
    testing = state.get("testing_findings", {})
    files_analyzed = len(state.get("file_map", {}))

    llm_report = _synthesize_with_llm(
        structure=structure,
        security=security,
        quality=quality,
        testing=testing,
        files_analyzed=files_analyzed,
    )

    if llm_report and isinstance(llm_report, dict) and "overall_score" in llm_report:
        final_report = _normalize_report_shape(llm_report, files_analyzed)
        update_current_span(
            output={
                "overall_score": final_report.get("overall_score"),
                "top_3_fixes": final_report.get("top_3_fixes", []),
            }
        )
        return {"final_report": final_report}

    # Safe deterministic fallback when LLM output is malformed/unavailable.
    final_report = _build_deterministic_report(
        structure=structure,
        security=security,
        quality=quality,
        testing=testing,
        files_analyzed=files_analyzed,
    )
    update_current_span(
        output={
            "overall_score": final_report.get("overall_score"),
            "top_3_fixes": final_report.get("top_3_fixes", []),
        }
    )
    return {"final_report": final_report}


def _synthesize_with_llm(
    structure: dict,
    security: dict,
    quality: dict,
    testing: dict,
    files_analyzed: int,
) -> dict | None:
    prompt = f"""
Input findings:
- structure: {structure}
- security: {security}
- quality: {quality}
- testing: {testing}
- files_analyzed: {files_analyzed}

Return STRICT JSON with this schema:
{{
  "overall_score": <int 0-100>,
  "mega_verdict": "<1-2 sentence executive verdict>",
  "summary": "<brief summary>",
  "files_analyzed": <int>,
  "dimensions": {{
    "structure": {{
      "score": <int>,
      "findings": ["..."],
      "flagged_files": ["..."],
      "recommendations": ["..."]
    }},
    "security": {{
      "score": <int>,
      "findings": ["..."],
      "flagged_files": ["..."],
      "recommendations": ["..."]
    }},
    "quality": {{
      "score": <int>,
      "findings": ["..."],
      "flagged_files": ["..."],
      "recommendations": ["..."]
    }},
    "testing": {{
      "score": <int>,
      "findings": ["..."],
      "flagged_files": ["..."],
      "recommendations": ["..."]
    }}
  }},
  "top_3_fixes": ["...", "...", "..."],
  "all_recommendations": ["..."],
  "flagged_files": ["..."]
}}

Rules:
- Top 3 fixes must never be empty.
- Prioritize by severity + impact + effort.
- Use concrete file references where available.
- If uncertainty exists, say so in findings text.
"""
    out = call_llm_json(
        prompt=prompt,
        system_prompt=SYNTH_SYSTEM_PROMPT,
        model=settings.llm_model_synthesizer,
    )
    if isinstance(out, dict) and "error" not in out:
        return out
    return None


def _build_deterministic_report(
    structure: dict,
    security: dict,
    quality: dict,
    testing: dict,
    files_analyzed: int,
) -> dict:
    total = (
        structure.get("score", 0)
        + security.get("score", 0)
        + quality.get("score", 0)
        + testing.get("score", 0)
    ) // 4

    all_findings = (
        structure.get("findings", [])
        + security.get("findings", [])
        + quality.get("findings", [])
        + testing.get("findings", [])
    )

    flagged = list(
        set(
            structure.get("flagged_files", [])
            + security.get("flagged_files", [])
            + quality.get("flagged_files", [])
            + testing.get("flagged_files", [])
        )
    )

    structure_rec = structure.get("recommendations", [])
    security_rec = security.get("recommendations", [])
    quality_rec = quality.get("recommendations", [])
    testing_rec = testing.get("recommendations", [])

    return {
        "overall_score": total,
        "files_analyzed": files_analyzed,
        "mega_verdict": build_mega_verdict(total, structure, security, quality, testing),
        "dimensions": {
            "structure": {
                "score": structure.get("score", 0),
                "findings": structure.get("findings", []),
                "flagged_files": structure.get("flagged_files", []),
                "recommendations": structure_rec,
            },
            "security": {
                "score": security.get("score", 0),
                "findings": security.get("findings", []),
                "flagged_files": security.get("flagged_files", []),
                "recommendations": security_rec,
            },
            "quality": {
                "score": quality.get("score", 0),
                "findings": quality.get("findings", []),
                "flagged_files": quality.get("flagged_files", []),
                "recommendations": quality_rec,
            },
            "testing": {
                "score": testing.get("score", 0),
                "findings": testing.get("findings", []),
                "flagged_files": testing.get("flagged_files", []),
                "recommendations": testing_rec,
            },
        },
        "top_3_fixes": generate_fixes(structure, security, quality, testing),
        "all_recommendations": dedupe_preserve_order(
            structure_rec + security_rec + quality_rec + testing_rec
        )[:12],
        "flagged_files": flagged,
        "summary": generate_summary(total, all_findings),
    }


def _normalize_report_shape(report: dict, files_analyzed: int) -> dict:
    report.setdefault("files_analyzed", files_analyzed)
    report.setdefault("top_3_fixes", [])
    report.setdefault("all_recommendations", [])
    report.setdefault("flagged_files", [])
    report.setdefault("summary", "")
    report.setdefault("mega_verdict", "")

    dims = report.get("dimensions", {})
    for key in ["structure", "security", "quality", "testing"]:
        dims.setdefault(key, {})
        dims[key].setdefault("score", 0)
        dims[key].setdefault("findings", [])
        dims[key].setdefault("flagged_files", [])
        dims[key].setdefault("recommendations", [])
    report["dimensions"] = dims

    if not report.get("top_3_fixes"):
        report["top_3_fixes"] = generate_fixes(
            dims.get("structure", {}),
            dims.get("security", {}),
            dims.get("quality", {}),
            dims.get("testing", {}),
        )
    return report


def generate_fixes(structure: dict, security: dict, quality: dict, testing: dict) -> list:
    fixes = []
    sf = _finding_texts(security.get("findings", []) or [])
    tf = _finding_texts(testing.get("findings", []) or [])
    qf = _finding_texts(quality.get("findings", []) or [])
    stf = _finding_texts(structure.get("findings", []) or [])

    rec_candidates = (
        (structure.get("recommendations", []) or [])
        + (security.get("recommendations", []) or [])
        + (quality.get("recommendations", []) or [])
        + (testing.get("recommendations", []) or [])
    )
    for rec in rec_candidates:
        if isinstance(rec, str) and rec.strip():
            fixes.append(rec.strip())

    if any("secret" in f.lower() or "key" in f.lower() for f in sf):
        fixes.append("Move secrets to environment variables")
    if any("token" in f.lower() for f in sf):
        fixes.append("Remove hardcoded tokens/secrets")
    if any("test" in f.lower() for f in tf):
        fixes.append("Add high-value tests for authentication, validation, and critical flows")
    if any("ci" in f.lower() for f in tf):
        fixes.append("Add CI workflow to run linting and tests on each pull request")
    if any("naming" in f.lower() or "complex" in f.lower() for f in qf):
        fixes.append("Refactor long/complex functions and improve naming clarity in flagged files")
    if any("separation" in f.lower() or "layer" in f.lower() for f in stf):
        fixes.append("Enforce layer boundaries (route-service-repository) and remove cross-layer leakage")

    if not fixes:
        scored = sorted(
            [
                ("structure", structure.get("score", 0)),
                ("security", security.get("score", 0)),
                ("quality", quality.get("score", 0)),
                ("testing", testing.get("score", 0)),
            ],
            key=lambda x: x[1],
        )
        for dim, _ in scored[:3]:
            if dim == "security":
                fixes.append("Add input validation, secret scanning, and explicit authz checks")
            elif dim == "testing":
                fixes.append("Create a baseline test suite for core business flows and error cases")
            elif dim == "quality":
                fixes.append("Reduce function complexity and remove duplication in hot paths")
            elif dim == "structure":
                fixes.append("Reorganize modules to improve cohesion and dependency direction")

    return dedupe_preserve_order(fixes)[:3]


def generate_summary(score: int, findings: list) -> str:
    finding_texts = _finding_texts(findings)
    if score >= 80:
        base = "Excellent codebase. Well structured with good practices."
    elif score >= 60:
        base = "Solid structure with minor improvements needed."
    elif score >= 40:
        base = "Good foundation but several areas need attention."
    else:
        base = "Requires significant improvements before production."

    if any("secret" in f.lower() for f in finding_texts):
        base += " Security hygiene needs immediate attention."
    if any("no test" in f.lower() for f in finding_texts):
        base += " Testing is a major gap."
    if any("no ci" in f.lower() for f in finding_texts):
        base += " CI/CD should be configured."

    return base


def dedupe_preserve_order(items: list) -> list:
    seen = set()
    out = []
    for item in items:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return out


def build_mega_verdict(total: int, structure: dict, security: dict, quality: dict, testing: dict) -> str:
    weakest = sorted(
        [
            ("structure", structure.get("score", 0)),
            ("security", security.get("score", 0)),
            ("quality", quality.get("score", 0)),
            ("testing", testing.get("score", 0)),
        ],
        key=lambda x: x[1],
    )
    weak_dims = ", ".join([f"{name}:{score}" for name, score in weakest[:2]])
    if total >= 80:
        return f"Strong engineering baseline. Maintain momentum by addressing weakest dimensions ({weak_dims})."
    if total >= 60:
        return f"Promising codebase with clear improvement paths. Prioritize weakest dimensions first ({weak_dims})."
    if total >= 40:
        return f"Usable foundation but not production-ready. Resolve weakest dimensions before feature acceleration ({weak_dims})."
    return f"High risk for maintainability and reliability. Focus immediately on weakest dimensions ({weak_dims}) before expansion."


def _finding_texts(findings: list) -> list[str]:
    texts: list[str] = []
    for item in findings:
        if isinstance(item, str):
            texts.append(item)
            continue
        if isinstance(item, dict):
            reason = item.get("reason")
            if isinstance(reason, str) and reason.strip():
                texts.append(reason.strip())
    return texts
