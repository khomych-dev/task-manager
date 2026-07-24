from datetime import datetime
from typing import Sequence
from uuid import UUID

import structlog
from fastapi import HTTPException, status

from app.models.task import Task, Comment
from app.models.user import User
from app.repositories.task import TaskRepository
from app.repositories.comment import CommentRepository
from app.repositories.workspace import WorkspaceRepository, WorkspaceMemberRepository
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskStatusUpdate,
    CommentCreate,
    TaskResponse,
    CommentResponse,
)
from app.websocket_manager import manager

logger = structlog.get_logger()


class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
        comment_repo: CommentRepository,
    ) -> None:
        self.task_repo = task_repo
        self.workspace_repo = workspace_repo
        self.member_repo = member_repo
        self.comment_repo = comment_repo

    async def _check_workspace_access(
        self, workspace_id: UUID, user_id: UUID, required_roles: list[str]
    ) -> None:
        """Verifying a user's access to the workspace."""
        member = await self.member_repo.get_by_workspace_and_user(workspace_id, user_id)
        if not member or member.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions in this workspace",
            )

    async def create(
        self, workspace_id: UUID, obj_in: TaskCreate, current_user: User
    ) -> Task:
        """Create a new task in the workspace."""
        await self._check_workspace_access(
            workspace_id, current_user.id, ["owner", "admin", "member"]
        )

        create_data = obj_in.model_dump()
        create_data["workspace_id"] = workspace_id
        create_data["creator_id"] = current_user.id

        task = await self.task_repo.create(create_data)
        logger.info(
            "task_created",
            task_id=str(task.id),
            workspace_id=str(task.workspace_id),
            creator_id=str(current_user.id),
        )

        # Broadcast the event when a task is created
        await manager.broadcast_to_workspace(
            workspace_id,
            {
                "event": "task.created",
                "task": TaskResponse.model_validate(task).model_dump(mode="json"),
            },
        )

        return task

    async def get_multi(
        self,
        workspace_id: UUID,
        current_user: User,
        status: str | None = None,
        priority: str | None = None,
        assignee_id: UUID | None = None,
        my: bool = False,
        deadline_before: datetime | None = None,
        tags: str | None = None,
        search: str | None = None,
        sort: str = "deadline",
        order: str = "asc",
        page: int = 1,
        per_page: int = 20,
    ) -> Sequence[Task]:
        """Get list of tasks with filters."""
        await self._check_workspace_access(
            workspace_id, current_user.id, ["owner", "admin", "member", "viewer"]
        )
        return await self.task_repo.get_multi_with_filters(
            workspace_id=workspace_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            my=my,
            current_user_id=current_user.id,
            deadline_before=deadline_before,
            tags=tags,
            search=search,
            sort=sort,
            order=order,
            page=page,
            per_page=per_page,
        )

    async def get(self, workspace_id: UUID, task_id: UUID, current_user: User) -> Task:
        """Get the details of a task."""
        await self._check_workspace_access(
            workspace_id, current_user.id, ["owner", "admin", "member", "viewer"]
        )
        task = await self.task_repo.get(task_id)
        if not task or task.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found in this workspace",
            )
        return task

    async def update(
        self, workspace_id: UUID, task_id: UUID, obj_in: TaskUpdate, current_user: User
    ) -> Task:
        """Update the fields of a task."""
        task = await self.get(workspace_id, task_id, current_user)

        # Checking permissions (members cannot edit other people's tasks)
        member = await self.member_repo.get_by_workspace_and_user(
            workspace_id, current_user.id
        )
        if member.role == "member" and task.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members can only edit their own tasks",
            )
        elif member.role not in ["owner", "admin", "member"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        update_data = obj_in.model_dump(exclude_unset=True)
        if update_data:
            task = await self.task_repo.update(task, update_data)
            logger.info("task_updated", task_id=str(task.id))

            # Broadcast the event when a task is updated
            await manager.broadcast_to_workspace(
                workspace_id,
                {
                    "event": "task.updated",
                    "task": TaskResponse.model_validate(task).model_dump(mode="json"),
                    "changed_fields": list(update_data.keys()),
                },
            )

        return task

    async def update_status(
        self,
        workspace_id: UUID,
        task_id: UUID,
        obj_in: TaskStatusUpdate,
        current_user: User,
    ) -> Task:
        """Separate method for changing status (in the future there will be a WebSocket broadcast)."""
        await self._check_workspace_access(
            workspace_id, current_user.id, ["owner", "admin", "member"]
        )
        task = await self.get(workspace_id, task_id, current_user)

        old_status = task.status
        task = await self.task_repo.update(task, {"status": obj_in.status})

        logger.info(
            "task_status_updated", task_id=str(task.id), new_status=obj_in.status
        )

        # Broadcast the event when a task status is changed
        await manager.broadcast_to_workspace(
            workspace_id,
            {
                "event": "task.status_changed",
                "task_id": str(task.id),
                "old": old_status,
                "new": obj_in.status,
            },
        )

        return task

    async def delete(
        self, workspace_id: UUID, task_id: UUID, current_user: User
    ) -> None:
        """Delete a task."""
        task = await self.get(workspace_id, task_id, current_user)
        await self._check_workspace_access(
            workspace_id, current_user.id, ["owner", "admin"]
        )
        await self.task_repo.delete(task.id)
        logger.info("task_deleted", task_id=str(task.id))

        # Broadcast the event when a task is deleted
        await manager.broadcast_to_workspace(
            workspace_id,
            {
                "event": "task.deleted",
                "task_id": str(task_id),
            },
        )

    async def create_comment(
        self,
        workspace_id: UUID,
        task_id: UUID,
        obj_in: CommentCreate,
        current_user: User,
    ) -> Comment:
        """Add a comment to a task."""
        await self.get(
            workspace_id, task_id, current_user
        )  # Checking if the task exists and if there is access to the workspace
        await self._check_workspace_access(
            workspace_id, current_user.id, ["owner", "admin", "member"]
        )

        create_data = obj_in.model_dump()
        create_data["task_id"] = task_id
        create_data["author_id"] = current_user.id

        comment = await self.comment_repo.create(create_data)
        logger.info("comment_created", comment_id=str(comment.id), task_id=str(task_id))

        # Broadcast the event when a comment is added
        await manager.broadcast_to_workspace(
            workspace_id,
            {
                "event": "comment.created",
                "task_id": str(task_id),
                "comment": CommentResponse.model_validate(comment).model_dump(
                    mode="json"
                ),
            },
        )

        return comment

    async def get_comments(
        self,
        workspace_id: UUID,
        task_id: UUID,
        current_user: User,
        page: int = 1,
        per_page: int = 20,
    ) -> Sequence[Comment]:
        """Get comments for a task."""
        await self.get(workspace_id, task_id, current_user)  # Checking access
        skip = (page - 1) * per_page
        return await self.comment_repo.get_by_task_id(
            task_id, skip=skip, limit=per_page
        )

    async def delete_comment(
        self, task_id: UUID, comment_id: UUID, current_user: User
    ) -> None:
        """Delete a comment (only the author can do it)."""
        comment = await self.comment_repo.get(comment_id)
        if not comment or comment.task_id != task_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )

        if comment.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only author can delete their comment",
            )

        await self.comment_repo.delete(comment_id)
        logger.info("comment_deleted", comment_id=str(comment_id))
