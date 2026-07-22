from typing import Sequence
from uuid import UUID

from sqlalchemy import select, delete
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

    async def get_members(self, workspace_id: UUID) -> Sequence[WorkspaceMember]:
        """Retrieve all members of a workspace."""
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_member(
        self, workspace_id: UUID, user_id: UUID
    ) -> WorkspaceMember | None:
        """Retrieve a specific member of a workspace."""
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_member(self, workspace_id: UUID, user_id: UUID) -> None:
        """Remove a member from a workspace."""
        stmt = delete(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_member_role(
        self, workspace_id: UUID, user_id: UUID, role: str
    ) -> WorkspaceMember | None:
        """Update the role of a workspace member."""
        member = await self.get_member(workspace_id, user_id)
        if member:
            member.role = role
            await self.session.commit()
            await self.session.refresh(member)
        return member
