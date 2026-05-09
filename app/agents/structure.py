from app.agents.state import ReviewState


def structure_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]
    files = list(file_map.keys())

    issues = []
    flagged = []
    score = 70

    folders = set()
    for f in files:
        parts = f.split("/")
        if len(parts) > 1:
            folders.add(parts[0])

    folders_to_check = {"src", "lib", "app", "api", "services", "routes", "models", "utils", "tests"}
    found_folders = folders & folders_to_check

    if found_folders:
        issues.append(f"Found organized folders: {', '.join(found_folders)}")
        score += 10
    else:
        issues.append("No common source folders found (src/lib/app)")
        score -= 10

    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in files)
    if has_tests:
        issues.append("Tests folder present")
    else:
        issues.append("No test files detected in repo")
        flagged.append("root")

    state["structure_findings"] = {
        "score": max(0, min(100, score)),
        "findings": issues,
        "flagged_files": flagged
    }
    return state