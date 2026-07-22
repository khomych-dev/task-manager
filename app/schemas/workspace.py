from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class WorkspaceResponse(WorkspaceBase):
    id: UUID
    owner_id: UUID

    model_config = ConfigDict(from_attributes=True)
