from pydantic import BaseModel, HttpUrl
from typing import Optional


class ReviewRequest(BaseModel):
    repo_url: HttpUrl


class FileEntry(BaseModel):
    path: str
    type: str
    size: int | None = None


class FileContent(BaseModel):
    path: str
    content: str


class RepoTreeResponse(BaseModel):
    owner: str
    repo: str
    total_discovered: int
    total_returned: int
    truncated: bool
    files: list[FileEntry]


class DimensionResult(BaseModel):
    score: int
    findings: list[str]
    flagged_files: list[str]


class ReviewResponse(BaseModel):
    id: int
    repo_url: str
    status: str
    report: Optional[dict] = None
