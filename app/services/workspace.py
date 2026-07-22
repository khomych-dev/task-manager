import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID

import structlog
from fastapi import HTTPException, status
from fastapi_mail import MessageSchema, MessageType

from app.core.config import settings
from app.core.email import fast_mail
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceInviteCreate,
    WorkspaceUpdate,
)

logger = structlog.get_logger()


class WorkspaceService:
    def __init__(self, workspace_repo: WorkspaceRepository) -> None:
        self.workspace_repo = workspace_repo

    async def create(self, obj_in: WorkspaceCreate, current_user: User) -> Workspace:
        """Create a new workspace."""
        create_data = obj_in.model_dump()
        create_data["owner_id"] = current_user.id

        workspace = await self.workspace_repo.create(create_data)

        await self.workspace_repo.add_member(workspace.id, current_user.id, "owner")

        logger.info(
            "workspace_created",
            workspace_id=str(workspace.id),
            owner_id=str(current_user.id),
        )
        return workspace

    async def get_user_workspaces(self, user_id: UUID) -> Sequence[Workspace]:
        """Get all workspaces where the user is a member."""
        return await self.workspace_repo.get_by_user_id(user_id)

    async def get(self, workspace_id: UUID, current_user: User) -> Workspace:
        """Get a specific workspace."""
        workspace = await self.workspace_repo.get(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
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

    async def get_members(self, workspace_id: UUID) -> Sequence[WorkspaceMember]:
        """Get all members of a workspace."""
        return await self.workspace_repo.get_members(workspace_id)

    async def update_member_role(
        self, workspace_id: UUID, user_id: UUID, role: str
    ) -> WorkspaceMember:
        """Update a member's role."""
        member = await self.workspace_repo.update_member_role(
            workspace_id, user_id, role
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
            )
        return member

    async def remove_member(self, workspace_id: UUID, user_id: UUID) -> None:
        """Remove a member or leave a workspace."""
        member = await self.workspace_repo.get_member(workspace_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
            )

        if member.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner cannot be removed or leave. Delete the workspace instead.",
            )

        await self.workspace_repo.remove_member(workspace_id, user_id)

    async def invite_member(
        self, workspace_id: UUID, obj_in: WorkspaceInviteCreate
    ) -> None:
        """Generate token, save invitation, and send email."""
        token = uuid.uuid4().hex
        # Токен дійсний 7 днів
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        await self.workspace_repo.create_invitation(
            workspace_id=workspace_id,
            email=obj_in.email,
            role=obj_in.role,
            token=token,
            expires_at=expires_at,
        )

        invite_link = f"{settings.frontend_url}/invitations/accept?token={token}"

        message = MessageSchema(
            subject="Запрошення у Workspace",
            recipients=[obj_in.email],
            body=f"Ви отримали запрошення. Перейдіть за посиланням, щоб прийняти: {invite_link}",
            subtype=MessageType.html,
        )

        try:
            await fast_mail.send_message(message)
            logger.info(
                "invitation_email_sent",
                email=obj_in.email,
                workspace_id=str(workspace_id),
            )
        except Exception as e:
            # Оскільки у тебе фейкові дані SMTP, ми просто логуємо помилку і не видаємо 500 статус
            logger.error("email_send_failed", error=str(e), email=obj_in.email)

    async def accept_invitation(self, token: str, current_user: User) -> None:
        """Accept an invitation using the token."""
        invitation = await self.workspace_repo.get_invitation_by_token(token)

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        if invitation.accepted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation already accepted",
            )

        if invitation.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired"
            )

        existing_member = await self.workspace_repo.get_member(
            invitation.workspace_id, current_user.id
        )
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member",
            )

        await self.workspace_repo.add_member(
            invitation.workspace_id, current_user.id, invitation.role
        )
        await self.workspace_repo.mark_invitation_accepted(invitation)

        logger.info(
            "invitation_accepted",
            user_id=str(current_user.id),
            workspace_id=str(invitation.workspace_id),
        )
