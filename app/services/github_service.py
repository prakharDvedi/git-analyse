import base64
import logging
import time
import requests

from app.core.settings import get_settings
from app.core.telemetry import elapsed_ms, get_logger, log_event

GITHUB_API_BASE = "https://api.github.com"
MAX_FILES = 50
MAX_FILE_BYTES = 200_000
logger = get_logger("app.services.github")


def _headers() -> dict:
    settings = get_settings()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "CodeReviewer",
    }
    if settings.github_token:
        headers["Authorization"] = f"token {settings.github_token}"
    return headers


def get_default_branch(owner: str, repo: str) -> str:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    started = time.perf_counter()
    log_event(logger, logging.INFO, "github.repo.started", owner=owner, repo=repo)
    resp = requests.get(url, headers=_headers(), timeout=20)
    if resp.status_code == 404:
        log_event(
            logger,
            logging.WARNING,
            "github.repo.not_found",
            owner=owner,
            repo=repo,
            status_code=resp.status_code,
            execution_duration_ms=elapsed_ms(started),
        )
        raise ValueError("Repository not found or not public")
    resp.raise_for_status()
    log_event(
        logger,
        logging.INFO,
        "github.repo.succeeded",
        owner=owner,
        repo=repo,
        status_code=resp.status_code,
        execution_duration_ms=elapsed_ms(started),
    )
    return resp.json()["default_branch"]


def get_repo_tree(owner: str, repo: str, branch: str) -> tuple[list[dict], int, bool]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    started = time.perf_counter()
    log_event(logger, logging.INFO, "github.tree.started", owner=owner, repo=repo, branch=branch)
    resp = requests.get(url, headers=_headers(), timeout=30)
    if resp.status_code == 404:
        log_event(
            logger,
            logging.WARNING,
            "github.tree.not_found",
            owner=owner,
            repo=repo,
            branch=branch,
            status_code=resp.status_code,
            execution_duration_ms=elapsed_ms(started),
        )
        raise ValueError("Repository tree not found")
    resp.raise_for_status()

    tree = resp.json().get("tree", [])
    file_entries = [x for x in tree if x.get("type") == "blob"]

    total = len(file_entries)
    limited = file_entries[:MAX_FILES]
    truncated = total > MAX_FILES
    log_event(
        logger,
        logging.INFO,
        "github.tree.succeeded",
        owner=owner,
        repo=repo,
        branch=branch,
        total_discovered=total,
        total_returned=len(limited),
        truncated=truncated,
        execution_duration_ms=elapsed_ms(started),
    )
    return limited, total, truncated


def get_file_content(owner: str, repo: str, path: str) -> str:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    started = time.perf_counter()
    log_event(logger, logging.DEBUG, "github.file.started", owner=owner, repo=repo, path=path)
    resp = requests.get(url, headers=_headers(), timeout=20)
    if resp.status_code == 404:
        log_event(
            logger,
            logging.WARNING,
            "github.file.not_found",
            owner=owner,
            repo=repo,
            path=path,
            status_code=resp.status_code,
            execution_duration_ms=elapsed_ms(started),
        )
        raise ValueError(f"File not found: {path}")
    resp.raise_for_status()

    payload = resp.json()
    if isinstance(payload, list):
        log_event(logger, logging.WARNING, "github.file.invalid_path_type", path=path)
        raise ValueError(f"Path is not a file: {path}")

    file_size = payload.get("size")
    if isinstance(file_size, int) and file_size > MAX_FILE_BYTES:
        log_event(
            logger,
            logging.WARNING,
            "github.file.too_large",
            path=path,
            file_size=file_size,
            max_allowed=MAX_FILE_BYTES,
        )
        raise ValueError(f"File too large ({file_size} bytes): {path}")

    if payload.get("encoding") != "base64":
        log_event(
            logger,
            logging.WARNING,
            "github.file.unsupported_encoding",
            path=path,
            encoding=payload.get("encoding"),
        )
        raise ValueError(f"Unsupported file encoding for: {path}")

    raw = base64.b64decode(payload["content"])
    decoded = raw.decode("utf-8", errors="replace")
    log_event(
        logger,
        logging.DEBUG,
        "github.file.succeeded",
        path=path,
        content_length=len(decoded),
        execution_duration_ms=elapsed_ms(started),
    )
    return decoded
