from app.agents.state import ReviewState


TEST_PATTERNS = [
    "test_", "_test.", "spec_", ".spec.", "tests/", "__tests__/", "test/"
]


def testing_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]
    files = list(file_map.keys())

    test_files = []
    ci_config = []
    score = 20

    for f in files:
        fname = f.lower()
        if any(p in fname for p in TEST_PATTERNS):
            test_files.append(f)
        if "github" in fname and ("workflow" in fname or fname == ".github/workflows/") or fname.endswith((".yml", ".yaml")):
            ci_config.append(f)

    if test_files:
        score = min(100, 40 + len(test_files) * 10)
        issues = [f"Found {len(test_files)} test files"]
    else:
        issues = ["No test files found"]

    ci_files = [f for f in files if ".github" in f or "workflows" in f]
    if ci_files:
        issues.append("CI configuration present")
        score += 20
    else:
        issues.append("No CI configuration found")

    state["testing_findings"] = {
        "score": max(0, min(100, score)),
        "findings": issues,
        "flagged_files": test_files
    }
    return state