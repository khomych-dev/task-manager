import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class WorkspaceBase(BaseModel):
    title: str
    description: str | None = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class WorkspaceResponse(WorkspaceBase):
    id: uuid.UUID
    owner_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class MemberResponse(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceInviteCreate(BaseModel):
    email: str
    role: str = Field(pattern="^(admin|member|viewer)$")


class WorkspaceMemberUpdate(BaseModel):
    role: str = Field(pattern="^(owner|admin|member|viewer)$")
