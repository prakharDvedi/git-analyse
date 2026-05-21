from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    repo_url: str


class AnalysisSummary(BaseModel):
    id: int
    repo_url: str
    status: str
    created_at: datetime


class AnalysisDetail(AnalysisSummary):
    report: dict[str, Any] | None = None
