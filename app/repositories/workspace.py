from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Workspace, session)

    async def get_by_slug(self, slug: str) -> Workspace | None:
        """Retrieve a workspace by its unique slug."""
        stmt = select(Workspace).where(Workspace.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: UUID) -> Sequence[Workspace]:
        """Retrieve all workspaces owned by a specific user."""
        stmt = select(Workspace).where(Workspace.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
