from fastapi import FastAPI

# Core
from app.core.settings import get_settings

# DB
from app.db import engine
from app.models.base import Base
from app.models import user  # ensures models are registered

# Routers
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.users import router as users_router
from app.api.routes.review import router as review_router



settings = get_settings()

app = FastAPI(title=settings.app_name)


# Create tables
Base.metadata.create_all(bind=engine)


# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(review_router)


@app.get("/")
async def root():
    return {"message": "GitAnalyse API"}