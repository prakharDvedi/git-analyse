import logging
import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status

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


@router.websocket("/ws")
async def stream_analysis(ws: WebSocket):
    await ws.accept()
    try:
        init = await ws.receive_json()
        repo_url = init.get("repo_url")
        if not repo_url:
            await ws.send_json({"type": "error", "message": "repo_url is required"})
            await ws.close(code=1008)
            return

        await ws.send_json({"type": "status", "message": "analysis_started"})
        result = run_review(repo_url)
        payload = json.dumps(result)

        chunk_size = 120
        for i in range(0, len(payload), chunk_size):
            await ws.send_json({"type": "token", "data": payload[i : i + chunk_size]})
            await asyncio.sleep(0.01)

        await ws.send_json({"type": "done"})
        await ws.close()
    except Exception as e:
        await ws.send_json({"type": "error", "message": f"analysis_failed: {str(e)}"})
        await ws.close(code=1011)
