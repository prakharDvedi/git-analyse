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

    state["final_report"] = {
        "overall_score": total,
        "files_analyzed": len(state.get("file_map", {})),
        "dimensions": {
            "structure": {
                "score": structure.get("score", 0),
                "findings": structure.get("findings", []),
                "flagged_files": structure.get("flagged_files", [])
            },
            "security": {
                "score": security.get("score", 0),
                "findings": security.get("findings", []),
                "flagged_files": security.get("flagged_files", [])
            },
            "quality": {
                "score": quality.get("score", 0),
                "findings": quality.get("findings", []),
                "flagged_files": quality.get("flagged_files", [])
            },
            "testing": {
                "score": testing.get("score", 0),
                "findings": testing.get("findings", []),
                "flagged_files": testing.get("flagged_files", [])
            }
        },
        "top_3_fixes": generate_fixes(security, testing),
        "summary": generate_summary(total, all_findings)
    }
    return state


def generate_fixes(security: dict, testing: dict) -> list:
    fixes = []
    sf = security.get("findings", [])
    tf = testing.get("findings", [])

    if any("secret" in f.lower() or "key" in f.lower() for f in sf):
        fixes.append("Move secrets to environment variables")
    if any("token" in f.lower() for f in sf):
        fixes.append("Remove hardcoded tokens/secrets")
    if "No test files found" in tf:
        fixes.append("Add test files with coverage")
    if "No CI configuration found" in tf:
        fixes.append("Add GitHub Actions workflow")

    return fixes[:3]


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