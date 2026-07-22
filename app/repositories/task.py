from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Task, session)

    async def get_by_workspace(self, workspace_id: UUID) -> Sequence[Task]:
        """Retrieve all tasks for a specific workspace."""
        stmt = select(Task).where(Task.workspace_id == workspace_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_assignee(self, assignee_id: UUID) -> Sequence[Task]:
        """Retrieve all tasks assigned to a specific user."""
        stmt = select(Task).where(Task.assignee_id == assignee_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
