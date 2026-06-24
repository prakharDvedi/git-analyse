import logging
import time

from langfuse import observe
from github import Github
from github.GithubException import GithubException

from app.core.settings import get_settings
from app.core.telemetry import elapsed_ms, get_logger, log_event

MAX_FILES = 50
MAX_FILE_BYTES = 200_000
logger = get_logger("app.services.github")


def _client() -> Github:
    settings = get_settings()
    if settings.github_token:
        return Github(settings.github_token)
    return Github()


@observe(name="github.get_default_branch", as_type="span", capture_input=True, capture_output=False)
def get_default_branch(owner: str, repo: str) -> str:
    started = time.perf_counter()
    log_event(logger, logging.INFO, "github.repo.started", owner=owner, repo=repo)
    try:
        gh_repo = _client().get_repo(f"{owner}/{repo}")
    except GithubException as exc:
        status_code = getattr(exc, "status", None)
        log_event(
            logger,
            logging.WARNING,
            "github.repo.not_found",
            owner=owner,
            repo=repo,
            status_code=status_code,
            execution_duration_ms=elapsed_ms(started),
        )
        raise ValueError("Repository not found or not public")

    log_event(
        logger,
        logging.INFO,
        "github.repo.succeeded",
        owner=owner,
        repo=repo,
        status_code=200,
        execution_duration_ms=elapsed_ms(started),
    )
    return gh_repo.default_branch


@observe(name="github.get_repo_tree", as_type="span", capture_input=True, capture_output=False)
def get_repo_tree(owner: str, repo: str, branch: str) -> tuple[list[dict], int, bool]:
    started = time.perf_counter()
    log_event(logger, logging.INFO, "github.tree.started", owner=owner, repo=repo, branch=branch)
    try:
        gh_repo = _client().get_repo(f"{owner}/{repo}")
        tree = gh_repo.get_git_tree(branch, recursive=True)
    except GithubException as exc:
        status_code = getattr(exc, "status", None)
        log_event(
            logger,
            logging.WARNING,
            "github.tree.not_found",
            owner=owner,
            repo=repo,
            branch=branch,
            status_code=status_code,
            execution_duration_ms=elapsed_ms(started),
        )
        raise ValueError("Repository tree not found")

    file_entries = [
        {"path": item.path, "type": item.type, "size": item.size}
        for item in tree.tree
        if item.type == "blob"
    ]

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


@observe(name="github.get_file_content", as_type="span", capture_input=True, capture_output=False)
def get_file_content(owner: str, repo: str, path: str) -> str:
    started = time.perf_counter()
    log_event(logger, logging.DEBUG, "github.file.started", owner=owner, repo=repo, path=path)
    try:
        gh_repo = _client().get_repo(f"{owner}/{repo}")
        content_file = gh_repo.get_contents(path)
    except GithubException as exc:
        status_code = getattr(exc, "status", None)
        log_event(
            logger,
            logging.WARNING,
            "github.file.not_found",
            owner=owner,
            repo=repo,
            path=path,
            status_code=status_code,
            execution_duration_ms=elapsed_ms(started),
        )
        raise ValueError(f"File not found: {path}")

    if isinstance(content_file, list):
        raise ValueError(f"Path is not a file: {path}")

    file_size = content_file.size
    if file_size > MAX_FILE_BYTES:
        log_event(
            logger,
            logging.WARNING,
            "github.file.too_large",
            path=path,
            file_size=file_size,
            max_allowed=MAX_FILE_BYTES,
        )
        raise ValueError(f"File too large ({file_size} bytes): {path}")

    decoded = content_file.decoded_content.decode("utf-8", errors="replace")
    log_event(
        logger,
        logging.DEBUG,
        "github.file.succeeded",
        path=path,
        content_length=len(decoded),
        execution_duration_ms=elapsed_ms(started),
    )
    return decoded
