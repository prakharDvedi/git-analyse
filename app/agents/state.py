from typing import TypedDict, Optional


class ReviewState(TypedDict):
    repo_url: str
    file_map: dict
    selected_agents: Optional[list[str]]
    router_notes: Optional[dict]
    structure_findings: Optional[dict]
    security_findings: Optional[dict]
    quality_findings: Optional[dict]
    testing_findings: Optional[dict]
    final_report: Optional[dict]
