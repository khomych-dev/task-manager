import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None)
    status: Literal["todo", "in_progress", "review", "done"] = Field(default="todo")
    priority: Literal["low", "medium", "high", "critical"] = Field(default="medium")
    deadline: datetime.datetime | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)


class TaskCreate(TaskBase):
    assignee_id: UUID | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None)
    status: Literal["todo", "in_progress", "review", "done"] | None = Field(
        default=None
    )
    priority: Literal["low", "medium", "high", "critical"] | None = Field(default=None)
    deadline: datetime.datetime | None = Field(default=None)
    assignee_id: UUID | None = Field(default=None)
    tags: list[str] | None = Field(default=None)


class TaskStatusUpdate(BaseModel):
    status: Literal["todo", "in_progress", "review", "done"]


class TaskResponse(TaskBase):
    id: UUID
    workspace_id: UUID
    creator_id: UUID
    assignee_id: UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class CommentBase(BaseModel):
    text: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: UUID
    task_id: UUID
    author_id: UUID
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
