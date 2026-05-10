import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.core.telemetry import get_logger, log_event
from app.schemas.review import FileContent, FileEntry, RepoTreeResponse, ReviewRequest
from app.services.github_service import (
    get_default_branch,
    get_file_content,
    get_repo_tree,
)
from app.utils.repo_url import parse_github_repo_url

router = APIRouter(prefix="/review", tags=["review"])
logger = get_logger("app.api.routes.review")


@router.post("/tree", response_model=RepoTreeResponse)
def fetch_repo_tree(payload: ReviewRequest):
    log_event(logger, logging.INFO, "review.tree.started")
    try:
        owner, repo = parse_github_repo_url(str(payload.repo_url))
        branch = get_default_branch(owner, repo)
        files, total, truncated = get_repo_tree(owner, repo, branch)
        log_event(
            logger,
            logging.INFO,
            "review.tree.succeeded",
            owner=owner,
            repo=repo,
            total_discovered=total,
            total_returned=len(files),
            truncated=truncated,
        )

        return RepoTreeResponse(
            owner=owner,
            repo=repo,
            total_discovered=total,
            total_returned=len(files),
            truncated=truncated,
            files=[
                FileEntry(path=f["path"], type="file", size=f.get("size"))
                for f in files
            ],
        )
    except ValueError as e:
        log_event(logger, logging.WARNING, "review.tree.rejected", reason=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as exc:
        log_event(logger, logging.ERROR, "review.tree.failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch repository data from GitHub",
        )


@router.post("/file", response_model=FileContent)
def fetch_file_content(
    payload: ReviewRequest,
    path: str = Query(..., description="Repository file path"),
):
    log_event(logger, logging.INFO, "review.file.started", path=path)
    try:
        owner, repo = parse_github_repo_url(str(payload.repo_url))
        content = get_file_content(owner, repo, path)
        log_event(
            logger,
            logging.DEBUG,
            "review.file.succeeded",
            owner=owner,
            repo=repo,
            path=path,
            content_length=len(content),
        )
        return FileContent(path=path, content=content)
    except ValueError as e:
        log_event(logger, logging.WARNING, "review.file.rejected", path=path, reason=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as exc:
        log_event(logger, logging.ERROR, "review.file.failed", path=path, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch file content from GitHub",
        )
