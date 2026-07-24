from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Task, session)

    async def get_multi_with_filters(
        self,
        workspace_id: UUID,
        *,
        status: str | None = None,
        priority: str | None = None,
        assignee_id: UUID | None = None,
        my: bool = False,
        current_user_id: UUID | None = None,
        deadline_before: datetime | None = None,
        tags: str | None = None,
        search: str | None = None,
        sort: str = "deadline",
        order: str = "asc",
        page: int = 1,
        per_page: int = 20,
    ) -> Sequence[Task]:
        """Отримати список задач з фільтрами, сортуванням та пагінацією."""
        stmt = select(Task).where(Task.workspace_id == workspace_id)

        if status:
            statuses = [s.strip() for s in status.split(",")]
            stmt = stmt.where(Task.status.in_(statuses))

        if priority:
            priorities = [p.strip() for p in priority.split(",")]
            stmt = stmt.where(Task.priority.in_(priorities))

        if assignee_id:
            stmt = stmt.where(Task.assignee_id == assignee_id)

        if my and current_user_id:
            stmt = stmt.where(Task.assignee_id == current_user_id)

        if deadline_before:
            stmt = stmt.where(Task.deadline <= deadline_before)

        if tags:
            tags_list = [t.strip() for t in tags.split(",")]
            stmt = stmt.where(Task.tags.contains(tags_list))

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                )
            )

        sort_column = getattr(Task, sort, Task.created_at)
        if order.lower() == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))

        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        result = await self.session.execute(stmt)
        return result.scalars().all()
