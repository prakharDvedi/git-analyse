from app.agents.state import ReviewState


def synthesizer_node(state: ReviewState) -> ReviewState:
    structure = state.get("structure_findings", {})
    security = state.get("security_findings", {})
    quality = state.get("quality_findings", {})
    testing = state.get("testing_findings", {})

    total = (
        structure.get("score", 0) +
        security.get("score", 0) +
        quality.get("score", 0) +
        testing.get("score", 0)
    ) // 4

    all_findings = (
        structure.get("findings", []) +
        security.get("findings", []) +
        quality.get("findings", []) +
        testing.get("findings", [])
    )

    flagged = list(set(
        structure.get("flagged_files", []) +
        security.get("flagged_files", []) +
        quality.get("flagged_files", []) +
        testing.get("flagged_files", [])
    ))

    structure_rec = structure.get("recommendations", [])
    security_rec = security.get("recommendations", [])
    quality_rec = quality.get("recommendations", [])
    testing_rec = testing.get("recommendations", [])

    state["final_report"] = {
        "overall_score": total,
        "files_analyzed": len(state.get("file_map", {})),
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
            }
        },
        "top_3_fixes": generate_fixes(structure, security, quality, testing),
        "all_recommendations": dedupe_preserve_order(
            structure_rec + security_rec + quality_rec + testing_rec
        )[:12],
        "flagged_files": flagged,
        "summary": generate_summary(total, all_findings)
    }
    return state


def generate_fixes(structure: dict, security: dict, quality: dict, testing: dict) -> list:
    fixes = []
    sf = security.get("findings", []) or []
    tf = testing.get("findings", []) or []
    qf = quality.get("findings", []) or []
    stf = structure.get("findings", []) or []

    # Pull concrete recommendation candidates from all dimensions first.
    rec_candidates = (
        structure.get("recommendations", []) or []
    ) + (
        security.get("recommendations", []) or []
    ) + (
        quality.get("recommendations", []) or []
    ) + (
        testing.get("recommendations", []) or []
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

    # Ensure non-empty, useful top-3 even when agent text is sparse.
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
    if score >= 80:
        base = "Excellent codebase. Well structured with good practices."
    elif score >= 60:
        base = "Solid structure with minor improvements needed."
    elif score >= 40:
        base = "Good foundation but several areas need attention."
    else:
        base = "Requires significant improvements before production."

    if any("secret" in f.lower() for f in findings):
        base += " Security hygiene needs immediate attention."
    if any("no test" in f.lower() for f in findings):
        base += " Testing is a major gap."
    if any("no ci" in f.lower() for f in findings):
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
