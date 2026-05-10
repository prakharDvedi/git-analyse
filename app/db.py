import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import get_settings
from app.core.telemetry import get_logger, log_event

settings = get_settings()
logger = get_logger("app.db")

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    log_event(logger, logging.DEBUG, "db.session.open")
    db = SessionLocal()
    try:
        yield db
    finally:
        log_event(logger, logging.DEBUG, "db.session.close")
        db.close()
