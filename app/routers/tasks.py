from datetime import datetime
from typing import Annotated, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.task import Task, Comment
from app.models.user import User
from app.repositories.task import TaskRepository
from app.repositories.comment import CommentRepository
from app.repositories.workspace import WorkspaceRepository, WorkspaceMemberRepository
from app.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TaskStatusUpdate,
    CommentCreate,
    CommentResponse,
)
from app.services.task import TaskService

router = APIRouter(prefix="", tags=["tasks"])


def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    task_repo = TaskRepository(session)
    workspace_repo = WorkspaceRepository(session)
    member_repo = WorkspaceMemberRepository(session)
    comment_repo = CommentRepository(session)
    return TaskService(task_repo, workspace_repo, member_repo, comment_repo)


@router.post(
    "/workspaces/{workspace_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    workspace_id: UUID,
    obj_in: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    """Create a new task."""
    return await task_service.create(workspace_id, obj_in, current_user)


@router.get("/workspaces/{workspace_id}/tasks", response_model=list[TaskResponse])
async def get_workspace_tasks(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    status: str | None = Query(None),
    priority: str | None = Query(None),
    assignee_id: UUID | None = Query(None),
    my: bool = Query(False),
    deadline_before: datetime | None = Query(None),
    tags: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("deadline"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    task_service: TaskService = Depends(get_task_service),
) -> Sequence[Task]:
    """Get list of tasks with filters and pagination."""
    return await task_service.get_multi(
        workspace_id,
        current_user,
        status,
        priority,
        assignee_id,
        my,
        deadline_before,
        tags,
        search,
        sort,
        order,
        page,
        per_page,
    )


@router.get("/workspaces/{workspace_id}/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    workspace_id: UUID,
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    """Get the details of a task."""
    return await task_service.get(workspace_id, task_id, current_user)


@router.patch("/workspaces/{workspace_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    workspace_id: UUID,
    task_id: UUID,
    obj_in: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    """Update the fields of a task."""
    return await task_service.update(workspace_id, task_id, obj_in, current_user)


@router.patch(
    "/workspaces/{workspace_id}/tasks/{task_id}/status", response_model=TaskResponse
)
async def update_task_status(
    workspace_id: UUID,
    task_id: UUID,
    obj_in: TaskStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    """Update the status of a task."""
    return await task_service.update_status(workspace_id, task_id, obj_in, current_user)


@router.delete(
    "/workspaces/{workspace_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_task(
    workspace_id: UUID,
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> None:
    """Delete a task."""
    await task_service.delete(workspace_id, task_id, current_user)


@router.post(
    "/workspaces/{workspace_id}/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    workspace_id: UUID,
    task_id: UUID,
    obj_in: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> Comment:
    """Add a comment."""
    return await task_service.create_comment(
        workspace_id, task_id, obj_in, current_user
    )


@router.get(
    "/workspaces/{workspace_id}/tasks/{task_id}/comments",
    response_model=list[CommentResponse],
)
async def get_comments(
    workspace_id: UUID,
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    task_service: TaskService = Depends(get_task_service),
) -> Sequence[Comment]:
    """List of comments."""
    return await task_service.get_comments(
        workspace_id, task_id, current_user, page, per_page
    )


@router.delete(
    "/tasks/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_comment(
    task_id: UUID,
    comment_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> None:
    """Delete your comment."""
    await task_service.delete_comment(task_id, comment_id, current_user)
