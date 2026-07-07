from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommentBase(BaseModel):
    text: str


class CommentResponse(CommentBase):
    id: UUID
    task_id: UUID
    author_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    deadline: datetime | None = None
    tags: list[str] = []


class TaskCreate(TaskBase):
    workspace_id: UUID


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    deadline: datetime | None = None
    tags: list[str] | None = None


class TaskResponse(TaskBase):
    id: UUID
    creator_id: UUID
    assignee_id: UUID | None
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
