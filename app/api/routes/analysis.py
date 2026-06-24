import json
import asyncio
import logging

from langfuse import observe
from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from sqlalchemy.orm import Session

from app.agents.pipeline import run_review
from app.api.deps import get_current_user
from app.core.langfuse import flush_langfuse, set_current_trace_io, update_current_span
from app.core.telemetry import elapsed_ms, get_logger, log_event, request_start_time
from app.db import get_db
from app.models.analysis import Analysis
from app.models.user import User
from app.schemas.analysis import AnalysisDetail, AnalysisSummary, AnalyzeRequest

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = get_logger("app.api.routes.analysis")


def _serialize_analysis(record: Analysis) -> AnalysisDetail:
    report = None
    if record.report_json:
        report = json.loads(record.report_json)
    return AnalysisDetail(
        id=record.id,
        repo_url=record.repo_url,
        status=record.status,
        error_message=record.error_message,
        created_at=record.created_at,
        report=report,
    )

@observe(name="analysis_request", as_type="chain", capture_input=False, capture_output=False)
@router.post("", response_model=AnalysisDetail, status_code=status.HTTP_201_CREATED)
def start_analysis(
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    started = request_start_time()
    log_event(logger, logging.INFO, "analysis.started", user_id=current_user.id)
    try:
        record = Analysis(
            user_id=current_user.id,
            repo_url=payload.repo_url,
            status="running",
            report_json=None,
            error_message=None,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        update_current_span(
            metadata={
                "analysis_id": record.id,
                "user_id": current_user.id,
                "repo_url": payload.repo_url,
                "status": "running",
            }
        )
        result = run_review(
            payload.repo_url,
            analysis_id=record.id,
            user_id=current_user.id,
        )
        record.status = "complete"
        record.report_json = json.dumps(result)
        record.error_message = None
        db.add(record)
        db.commit()
        set_current_trace_io(
            input={
                "repo_url": payload.repo_url,
                "analysis_id": record.id,
                "user_id": current_user.id,
            },
            output=_serialize_analysis(record),
        )
        log_event(
            logger,
            logging.INFO,
            "analysis.succeeded",
            user_id=current_user.id,
            analysis_id=record.id,
            overall_score=result.get("overall_score"),
            execution_duration_ms=elapsed_ms(started),
        )
        return _serialize_analysis(record)
    except Exception as e:
        db.rollback()
        update_current_span(level="ERROR", status_message=str(e))
        log_event(
            logger,
            logging.ERROR,
            "analysis.failed",
            user_id=current_user.id,
            error=str(e),
            execution_duration_ms=elapsed_ms(started),
        )
        try:
            if "record" in locals():
                record.status = "failed"
                record.error_message = str(e)
                db.add(record)
                db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Analysis failed: {str(e)}",
        )
    finally:
        flush_langfuse()


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc(), Analysis.id.desc())
        .all()
    )
    return [
        AnalysisSummary(
            id=record.id,
            repo_url=record.repo_url,
            status=record.status,
            error_message=record.error_message,
            created_at=record.created_at,
        )
        for record in records
    ]


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
        .first()
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return _serialize_analysis(record)


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
