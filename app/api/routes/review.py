from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.review import FileContent, FileEntry, RepoTreeResponse, ReviewRequest
from app.services.github_service import (
    get_default_branch,
    get_file_content,
    get_repo_tree,
)
from app.utils.repo_url import parse_github_repo_url

router = APIRouter(prefix="/review", tags=["review"])


@router.post("/tree", response_model=RepoTreeResponse)
def fetch_repo_tree(payload: ReviewRequest):
    try:
        owner, repo = parse_github_repo_url(str(payload.repo_url))
        branch = get_default_branch(owner, repo)
        files, total, truncated = get_repo_tree(owner, repo, branch)

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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch repository data from GitHub",
        )


@router.post("/file", response_model=FileContent)
def fetch_file_content(
    payload: ReviewRequest,
    path: str = Query(..., description="Repository file path"),
):
    try:
        owner, repo = parse_github_repo_url(str(payload.repo_url))
        content = get_file_content(owner, repo, path)
        return FileContent(path=path, content=content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch file content from GitHub",
        )
