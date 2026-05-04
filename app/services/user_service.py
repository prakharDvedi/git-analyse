from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repo import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)


def register_user(db: Session, email: str, username: str, password: str):
    if get_user_by_email(db, email):
        raise ValueError("Email already registered")
    if get_user_by_username(db, username):
        raise ValueError("Username already taken")

    hashed = hash_password(password)
    return create_user(db, email=email, username=username, hashed_password=hashed)


def login_user(db: Session, email: str, password: str) -> str:
    user = get_user_by_email(db, email)
    if not user:
        raise ValueError("Invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")

    return create_access_token(subject=str(user.id))
