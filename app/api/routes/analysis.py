from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.agents.pipeline import run_review
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.analysis import AnalyzeRequest
from app.schemas.review import ReviewResponse

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def start_analysis(
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    try:
        result = run_review(payload.repo_url)
        return ReviewResponse(
            id=1,
            repo_url=payload.repo_url,
            status="complete",
            report=result,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Analysis failed: {str(e)}",
        )