import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)
    status: str = Field(default="todo", max_length=50)
    priority: str = Field(default="medium", max_length=50)


class TaskCreate(TaskBase):
    workspace_id: UUID
    assignee_id: UUID | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None)
    status: str | None = Field(default=None, max_length=50)
    priority: str | None = Field(default=None, max_length=50)
    assignee_id: UUID | None = None


class TaskResponse(TaskBase):
    id: UUID
    workspace_id: UUID
    author_id: UUID
    assignee_id: UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)
