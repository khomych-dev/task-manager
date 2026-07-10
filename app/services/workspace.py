import re
import uuid
from typing import Sequence
from uuid import UUID

import structlog
from fastapi import HTTPException, status

from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate

logger = structlog.get_logger()


def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug with a unique suffix."""
    slug_base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug_base:
        slug_base = "workspace"
    unique_suffix = uuid.uuid4().hex[:6]
    return f"{slug_base}-{unique_suffix}"


class WorkspaceService:
    def __init__(self, workspace_repo: WorkspaceRepository) -> None:
        self.workspace_repo = workspace_repo

    async def create(self, obj_in: WorkspaceCreate, current_user: User) -> Workspace:
        """Create a new workspace."""
        slug = generate_slug(obj_in.name)

        create_data = obj_in.model_dump()
        create_data["slug"] = slug
        create_data["owner_id"] = current_user.id

        workspace = await self.workspace_repo.create(create_data)
        logger.info(
            "workspace_created",
            workspace_id=str(workspace.id),
            owner_id=str(current_user.id),
        )
        return workspace

    async def get_user_workspaces(self, user_id: UUID) -> Sequence[Workspace]:
        """Get all workspaces owned by the user."""
        return await self.workspace_repo.get_by_owner(user_id)

    async def get(self, workspace_id: UUID, current_user: User) -> Workspace:
        """Get a specific workspace, ensuring the user has access."""
        workspace = await self.workspace_repo.get(workspace_id)
        if not workspace or workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found or access denied",
            )
        return workspace

    async def update(
        self, workspace_id: UUID, obj_in: WorkspaceUpdate, current_user: User
    ) -> Workspace:
        """Update a workspace."""
        workspace = await self.get(workspace_id, current_user)
        update_data = obj_in.model_dump(exclude_unset=True)
        if update_data:
            workspace = await self.workspace_repo.update(workspace, update_data)
            logger.info("workspace_updated", workspace_id=str(workspace.id))
        return workspace

    async def delete(self, workspace_id: UUID, current_user: User) -> None:
        """Delete a workspace."""
        workspace = await self.get(workspace_id, current_user)
        await self.workspace_repo.delete(workspace.id)
        logger.info("workspace_deleted", workspace_id=str(workspace.id))
