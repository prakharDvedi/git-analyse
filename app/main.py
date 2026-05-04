from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.include_router(health_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the CodeReviewer API"}
