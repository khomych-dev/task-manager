from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace, WorkspaceMember
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

    async def get_by_user_id(self, user_id: UUID) -> Sequence[Workspace]:
        """Retrieve all workspaces where the user is a member."""
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_member(
        self, workspace_id: UUID, user_id: UUID, role: str
    ) -> WorkspaceMember:
        """Add a member to a workspace with a specific role."""
        member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
        self.session.add(member)
        await self.session.commit()
        return member
