from typing import Annotated, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.task import Task
from app.models.user import User
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    task_repo = TaskRepository(session)
    workspace_repo = WorkspaceRepository(session)
    return TaskService(task_repo, workspace_repo)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    obj_in: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    """Create a new task."""
    return await task_service.create(obj_in, current_user)


@router.get("/workspace/{workspace_id}", response_model=list[TaskResponse])
async def get_workspace_tasks(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> Sequence[Task]:
    """Get all tasks for a specific workspace."""
    return await task_service.get_workspace_tasks(workspace_id, current_user)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    """Get a specific task by ID."""
    return await task_service.get(task_id, current_user)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    obj_in: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    """Update a task."""
    return await task_service.update(task_id, obj_in, current_user)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
) -> None:
    """Delete a task."""
    await task_service.delete(task_id, current_user)
