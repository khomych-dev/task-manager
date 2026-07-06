from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from config import settings

# Creating an asynchronous engine. echo=True will output SQL queries to the console in development mode.
engine = create_async_engine(
    settings.database_url, echo=settings.environment == "development"
)

# Creating a session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for all future models (tables)
Base = declarative_base()


# Dependency for FastAPI to get the session in the routes
async def get_db():
    async with async_session_maker() as session:
        yield session
