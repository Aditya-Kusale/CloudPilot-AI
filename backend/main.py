"""FastAPI application entry point."""
from fastapi import FastAPI
from backend.api.routes.health import router as health_router
from backend.api.routes.sessions import router as sessions_router
from backend.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.2.0", description="Multi-cloud and DevOps intelligence platform.")
app.include_router(health_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "running", "docs": "/docs"}
