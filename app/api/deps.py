import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.core.telemetry import get_logger, log_event
from app.db import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
logger = get_logger("app.api.deps")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            log_event(logger, logging.WARNING, "auth.token.missing_subject")
            raise credentials_error
    except JWTError:
        log_event(logger, logging.WARNING, "auth.token.invalid")
        raise credentials_error

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        log_event(logger, logging.WARNING, "auth.token.user_not_found", user_id=user_id)
        raise credentials_error
    log_event(logger, logging.DEBUG, "auth.token.validated", user_id=user.id)
    return user
