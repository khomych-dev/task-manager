from fastapi import FastAPI
import structlog
from logger import setup_logging

# Let's initialize the logger before launching the application
setup_logging()
logger = structlog.get_logger()

app = FastAPI(title="Task Manager API")


@app.on_event("startup")
async def startup_event():
    await logger.ainfo("Application is starting up...", environment="development")


@app.get("/health")
async def health_check():
    await logger.ainfo("Health check endpoint hit")
    return {"status": "ok"}
