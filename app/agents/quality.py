import re
from app.agents.state import ReviewState


def count_lines(code: str) -> int:
    return len([l for l in code.split("\n") if l.strip() and not l.strip().startswith("#")])


def quality_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]

    issues = []
    flagged = []
    score = 70
    total_files = len(file_map)
    total_lines = 0
    long_functions = 0

    for path, content in file_map.items():
        if not path.endswith((".py", ".js", ".ts", ".tsx")):
            continue

        lines = count_lines(content)
        total_lines += lines

        if lines > 100:
            flagged.append(path)
            long_functions += 1

    if total_files > 0:
        avg_lines = total_lines // total_files
        if avg_lines > 50:
            issues.append(f"Average file length: {avg_lines} lines (could be split)")
        else:
            issues.append(f"Files are reasonably sized (avg {avg_lines} lines)")
            score += 10

    if long_functions > 0:
        issues.append(f"{long_functions} files over 100 lines - consider splitting")

    has_readme = any("readme" in f.lower() for f in file_map.keys())
    if not has_readme:
        issues.append("No README found")
        score -= 10

    state["quality_findings"] = {
        "score": max(0, min(100, score)),
        "findings": issues,
        "flagged_files": flagged
    }
    return state