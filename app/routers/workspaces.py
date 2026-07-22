from typing import Annotated, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
    MemberResponse,
    WorkspaceMemberUpdate,
)
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def get_workspace_service(
    session: AsyncSession = Depends(get_session),
) -> WorkspaceService:
    repo = WorkspaceRepository(session)
    return WorkspaceService(repo)


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    obj_in: WorkspaceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Workspace:
    """Create a new workspace."""
    return await workspace_service.create(obj_in, current_user)


@router.get("", response_model=list[WorkspaceResponse])
async def get_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Sequence[Workspace]:
    """Get all workspaces where the current user is a member."""
    return await workspace_service.get_user_workspaces(current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    _=Depends(require_role("viewer")),
) -> Workspace:
    """Get a specific workspace by ID."""
    return await workspace_service.get(workspace_id, current_user)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    obj_in: WorkspaceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    _=Depends(require_role("admin")),
) -> Workspace:
    """Update a workspace."""
    return await workspace_service.update(workspace_id, obj_in, current_user)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    _=Depends(require_role("owner")),
) -> None:
    """Delete a workspace."""
    await workspace_service.delete(workspace_id, current_user)


@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
async def get_workspace_members(
    workspace_id: UUID,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    _=Depends(require_role("viewer")),
) -> Sequence[WorkspaceMember]:
    """Get all members of a workspace."""
    return await workspace_service.get_members(workspace_id)


@router.patch("/{workspace_id}/members/{user_id}", response_model=MemberResponse)
async def update_workspace_member(
    workspace_id: UUID,
    user_id: UUID,
    obj_in: WorkspaceMemberUpdate,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    _=Depends(require_role("owner")),
) -> WorkspaceMember:
    """Update a member's role."""
    return await workspace_service.update_member_role(
        workspace_id, user_id, obj_in.role
    )


@router.delete(
    "/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_workspace_member(
    workspace_id: UUID,
    user_id: UUID,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    _=Depends(require_role("admin")),
) -> None:
    """Remove a member from the workspace."""
    await workspace_service.remove_member(workspace_id, user_id)


@router.delete("/{workspace_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_workspace(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    _=Depends(require_role("member")),
) -> None:
    """Leave a workspace."""
    await workspace_service.remove_member(workspace_id, current_user.id)
