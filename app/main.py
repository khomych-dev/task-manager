import sentry_sdk
import structlog
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI

from app.core.config import settings
from app.core.logger import setup_logging
from app.routers import auth, tasks, users, websocket, workspaces

# Let's initialize the logger before launching the application
setup_logging()
logger = structlog.get_logger()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=1.0,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await logger.ainfo(
        "Application is starting up...", environment=settings.environment
    )
    yield


app = FastAPI(title="Task Manager API", lifespan=lifespan)

# Connecting Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(workspaces.router)
app.include_router(tasks.router)
app.include_router(websocket.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    await logger.ainfo("Health check endpoint hit")
    return {"status": "ok"}
