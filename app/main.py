from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Core
from app.core.settings import get_settings
from app.core.telemetry import (
    correlation_id_ctx,
    elapsed_ms,
    get_logger,
    get_or_create_correlation_id,
    log_event,
    request_start_time,
    setup_logging,
)

# DB
from app.db import engine
from app.models.base import Base
from app.models import analysis, user  # ensures models are registered

# Routers
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.users import router as users_router
from app.api.routes.review import router as review_router
from app.api.routes.analysis import router as analysis_router



settings = get_settings()
setup_logging()
logger = get_logger("app.main")

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = get_or_create_correlation_id(request)
        token = correlation_id_ctx.set(correlation_id)
        started = request_start_time()

        try:
            response = await call_next(request)
            response.headers["x-correlation-id"] = correlation_id
            log_event(
                logger,
                level=20,
                message="request.completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                execution_duration_ms=elapsed_ms(started),
            )
            return response
        except Exception as exc:
            log_event(
                logger,
                level=40,
                message="request.failed",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                execution_duration_ms=elapsed_ms(started),
            )
            raise
        finally:
            correlation_id_ctx.reset(token)


app.add_middleware(RequestLoggingMiddleware)


# Create tables
Base.metadata.create_all(bind=engine)


# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(review_router)
app.include_router(analysis_router)


@app.get("/")
async def root():
    log_event(logger, level=20, message="root.pinged")
    return {"message": "GitAnalyse API"}
