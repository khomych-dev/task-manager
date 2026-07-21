import structlog
from fastapi import FastAPI

from app.core.logger import setup_logging
from app.routers import auth, tasks, users, workspaces

# Let's initialize the logger before launching the application
setup_logging()
logger = structlog.get_logger()

app = FastAPI(title="Task Manager API")

# Connecting Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(workspaces.router)
app.include_router(tasks.router)


@app.on_event("startup")
async def startup_event():
    await logger.ainfo("Application is starting up...", environment="development")


@app.get("/health")
async def health_check():
    await logger.ainfo("Health check endpoint hit")
    return {"status": "ok"}
