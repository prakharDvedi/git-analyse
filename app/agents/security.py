import re
from app.agents.state import ReviewState


SECRET_PATTERNS = [
    (r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]{20,}', "potential API key"),
    (r'secret["\']?\s*[:=]\s*["\']?[\w-]{20,}', "potential secret"),
    (r'password["\']?\s*[:=]\s*["\']?[^"\']{8,}', "hardcoded password"),
    (r'token["\']?\s*[:=]\s*["\']?[\w-]{20,}', "potential token"),
    (r'ghp_[\w]{36,}', "GitHub personal access token"),
    (r'github[_-]?token["\']?\s*[:=]', "GitHub token"),
]


def security_agent(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]

    issues = []
    flagged = []
    score = 80

    for path, content in file_map.items():
        for pattern, what in SECRET_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"{what} found in {path}")
                flagged.append(path)
                score -= 10
                break

    if not issues:
        issues.append("No obvious secrets detected")

    state["security_findings"] = {
        "score": max(0, min(100, score)),
        "findings": issues,
        "flagged_files": flagged
    }
    return state