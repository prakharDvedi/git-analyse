from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    repo_url: str