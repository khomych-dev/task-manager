from typing import Any, Generic, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

# Let's create a typed variable that is bound to our SQLAlchemy base class
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        It is initialized with a specific model (e.g., Workspace) and a database session.
        """
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> ModelType | None:
        """Get one record by UUID."""
        result = await self.session.execute(
            select(self.model).filter(self.model.id == id)
        )
        return result.scalars().first()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Get a list of records with pagination."""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """Create a new record from the passed dictionary."""
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        """Update an existing record."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: UUID) -> ModelType | None:
        """Delete a record by UUID."""
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
        return obj
