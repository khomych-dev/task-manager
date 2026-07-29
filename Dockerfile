FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Installing uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copying project files
COPY . .

# Install dependencies in a virtual environment (.venv)
RUN uv sync

# By default, we run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
