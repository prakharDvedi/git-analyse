import logging

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.core.telemetry import get_logger, log_event
from app.repositories.user_repo import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)

logger = get_logger("app.services.auth")


def register_user(db: Session, email: str, username: str, password: str):
    if get_user_by_email(db, email):
        log_event(logger, logging.WARNING, "auth.register.email_exists")
        raise ValueError("Email already registered")
    if get_user_by_username(db, username):
        log_event(logger, logging.WARNING, "auth.register.username_exists")
        raise ValueError("Username already taken")

    hashed = hash_password(password)
    log_event(logger, logging.DEBUG, "auth.register.password_hashed", hash_length=len(hashed))
    return create_user(db, email=email, username=username, hashed_password=hashed)


def login_user(db: Session, email: str, password: str) -> str:
    user = get_user_by_email(db, email)
    if not user:
        log_event(logger, logging.WARNING, "auth.login.user_not_found")
        raise ValueError("Invalid credentials")
    if not verify_password(password, user.hashed_password):
        log_event(logger, logging.WARNING, "auth.login.password_mismatch", user_id=user.id)
        raise ValueError("Invalid credentials")

    log_event(logger, logging.INFO, "auth.login.verified", user_id=user.id)
    return create_access_token(subject=str(user.id))
