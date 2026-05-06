import base64
import requests

GITHUB_API_BASE = "https://api.github.com"
MAX_FILES = 50


def _headers() -> dict:
    return {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "CodeReviewer",
    }


def get_default_branch(owner: str, repo: str) -> str:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    resp = requests.get(url, headers=_headers(), timeout=20)
    if resp.status_code == 404:
        raise ValueError("Repository not found or not public")
    resp.raise_for_status()
    return resp.json()["default_branch"]


def get_repo_tree(owner: str, repo: str, branch: str) -> tuple[list[dict], int, bool]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    resp = requests.get(url, headers=_headers(), timeout=30)
    if resp.status_code == 404:
        raise ValueError("Repository tree not found")
    resp.raise_for_status()

    tree = resp.json().get("tree", [])
    file_entries = [x for x in tree if x.get("type") == "blob"]

    total = len(file_entries)
    limited = file_entries[:MAX_FILES]
    truncated = total > MAX_FILES
    return limited, total, truncated


def get_file_content(owner: str, repo: str, path: str) -> str:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_headers(), timeout=20)
    if resp.status_code == 404:
        raise ValueError(f"File not found: {path}")
    resp.raise_for_status()

    payload = resp.json()
    if payload.get("encoding") != "base64":
        raise ValueError(f"Unsupported file encoding for: {path}")

    raw = base64.b64decode(payload["content"])
    return raw.decode("utf-8", errors="replace")
