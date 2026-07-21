from typing import Sequence
from uuid import UUID

import structlog
from fastapi import HTTPException, status

from app.models.task import Task
from app.models.user import User
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.task import TaskCreate, TaskUpdate

logger = structlog.get_logger()


class TaskService:
    def __init__(
        self, task_repo: TaskRepository, workspace_repo: WorkspaceRepository
    ) -> None:
        self.task_repo = task_repo
        self.workspace_repo = workspace_repo

    async def create(self, obj_in: TaskCreate, current_user: User) -> Task:
        """Create a new task in a workspace."""
        workspace = await self.workspace_repo.get(obj_in.workspace_id)
        if not workspace or workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found or access denied",
            )

        create_data = obj_in.model_dump()
        create_data["author_id"] = current_user.id

        task = await self.task_repo.create(create_data)
        logger.info(
            "task_created",
            task_id=str(task.id),
            workspace_id=str(task.workspace_id),
            author_id=str(current_user.id),
        )
        return task

    async def get_workspace_tasks(
        self, workspace_id: UUID, current_user: User
    ) -> Sequence[Task]:
        """Get all tasks for a specific workspace."""
        workspace = await self.workspace_repo.get(workspace_id)
        if not workspace or workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found or access denied",
            )
        return await self.task_repo.get_by_workspace(workspace_id)

    async def get(self, task_id: UUID, current_user: User) -> Task:
        """Get a specific task by ID."""
        task = await self.task_repo.get(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        workspace = await self.workspace_repo.get(task.workspace_id)
        if not workspace or workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this task",
            )

        return task

    async def update(
        self, task_id: UUID, obj_in: TaskUpdate, current_user: User
    ) -> Task:
        """Update a task."""
        task = await self.get(task_id, current_user)
        update_data = obj_in.model_dump(exclude_unset=True)
        if update_data:
            task = await self.task_repo.update(task, update_data)
            logger.info("task_updated", task_id=str(task.id))
        return task

    async def delete(self, task_id: UUID, current_user: User) -> None:
        """Delete a task."""
        task = await self.get(task_id, current_user)
        await self.task_repo.delete(task.id)
        logger.info("task_deleted", task_id=str(task.id))
