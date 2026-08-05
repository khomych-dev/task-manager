from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Creating an asynchronous engine. echo=True will output SQL queries to the console in development mode.
engine = create_async_engine(
    settings.database_url, echo=settings.environment == "development"
)

# Creating a session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Base class for all future models (tables)
class Base(DeclarativeBase):
    pass


# Dependency for FastAPI to get the session in the routes
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
