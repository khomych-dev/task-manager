from typing import Sequence
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Comment, session)

    async def get_by_task_id(
        self, task_id: UUID, skip: int = 0, limit: int = 20
    ) -> Sequence[Comment]:
        """Отримати список коментарів до задачі з пагінацією."""
        stmt = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(desc(Comment.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
