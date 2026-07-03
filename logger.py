import logging
import sys
import structlog

def setup_logging():
    # Configuring standard logging to intercept Uvicorn system messages
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            # ConsoleRenderer makes logs look nice in the terminal during development
            structlog.dev.ConsoleRenderer() 
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
