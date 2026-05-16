from pydantic import BaseModel, Field


class FindingItem(BaseModel):
    file: str = Field(min_length=1)
    reason: str = Field(min_length=5)
    evidence_snippet: str = Field(min_length=3)
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    confidence: float = Field(ge=0.0, le=1.0)


class AgentOutput(BaseModel):
    score: int = Field(ge=0, le=100)
    findings: list[FindingItem] = Field(default_factory=list)
    flagged_files: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

