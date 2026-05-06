from pydantic import BaseModel, HttpUrl


class ReviewRequest(BaseModel):
    repo_url: HttpUrl


class FileEntry(BaseModel):
    path: str
    type: str  # "file" | "dir"
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
