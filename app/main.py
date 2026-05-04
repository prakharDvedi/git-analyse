from fastapi import FastAPI

from app.api.routes.health import router as health_router

app = FastAPI(title="CodeReviewer")

app.include_router(health_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the CodeReviewer API"}