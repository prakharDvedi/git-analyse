import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.pipeline import run_review
from app.api.deps import get_current_user
from app.core.telemetry import elapsed_ms, get_logger, log_event, request_start_time
from app.models.user import User
from app.schemas.analysis import AnalyzeRequest
from app.schemas.review import ReviewResponse

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = get_logger("app.api.routes.analysis")


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def start_analysis(
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    started = request_start_time()
    log_event(logger, logging.INFO, "analysis.started", user_id=current_user.id)
    try:
        result = run_review(payload.repo_url)
        log_event(
            logger,
            logging.INFO,
            "analysis.succeeded",
            user_id=current_user.id,
            overall_score=result.get("overall_score"),
            execution_duration_ms=elapsed_ms(started),
        )
        return ReviewResponse(
            id=1,
            repo_url=payload.repo_url,
            status="complete",
            report=result,
        )
    except Exception as e:
        log_event(
            logger,
            logging.ERROR,
            "analysis.failed",
            user_id=current_user.id,
            error=str(e),
            execution_duration_ms=elapsed_ms(started),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Analysis failed: {str(e)}",
        )
