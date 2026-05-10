import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.telemetry import get_logger, log_event
from app.db import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import login_user, register_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("app.api.routes.auth")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    log_event(
        logger,
        logging.INFO,
        "auth.register.started",
        username_length=len(payload.username),
        password_length=len(payload.password),
    )
    try:
        user = register_user(
            db,
            email=payload.email,
            username=payload.username,
            password=payload.password,
        )
        log_event(logger, logging.INFO, "auth.register.succeeded", user_id=user.id)
        return user
    except ValueError as e:
        log_event(logger, logging.WARNING, "auth.register.rejected", reason=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    log_event(
        logger,
        logging.INFO,
        "auth.login.started",
        password_length=len(payload.password),
    )
    try:
        token = login_user(db, email=payload.email, password=payload.password)
        log_event(logger, logging.INFO, "auth.login.succeeded")
        return TokenResponse(access_token=token)
    except ValueError:
        log_event(logger, logging.WARNING, "auth.login.rejected", reason="invalid_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    log_event(logger, logging.DEBUG, "auth.me.fetched", user_id=current_user.id)
    return current_user
