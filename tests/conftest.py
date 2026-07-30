import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_session
from app.main import app

# Creating a URL for the test database
TEST_DATABASE_URL = str(settings.database_url).replace(
    "taskmanager", "taskmanager_test"
)

# Using NullPool for tests to avoid issues with the connection pool
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Creates an event loop instance for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Creates tables before tests and deletes after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a new database session for each test."""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Client for HTTP requests to API with overridden DB dependency."""

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
