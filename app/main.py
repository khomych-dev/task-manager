import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.logger import setup_logging
from app.routers import auth, tasks, users, websocket, workspaces

# Let's initialize the logger before launching the application
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await logger.ainfo("Application is starting up...", environment="development")
    yield


app = FastAPI(title="Task Manager API", lifespan=lifespan)

# Connecting Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(workspaces.router)
app.include_router(tasks.router)
app.include_router(websocket.router)


@app.get("/health")
async def health_check():
    await logger.ainfo("Health check endpoint hit")
    return {"status": "ok"}
