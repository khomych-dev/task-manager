from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Basic schema with fields sent by the client
class WorkspaceBase(BaseModel):
    name: str
    slug: str
    description: str | None = None


# Schema for creation (currently matches the base schema, but convenient for scaling)
class WorkspaceCreate(WorkspaceBase):
    pass


# Schema for returning workspace data through the API
class WorkspaceResponse(WorkspaceBase):
    id: UUID
    owner_id: UUID
    created_at: datetime

    # Allows Pydantic to read data directly from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)


# Schema for returning information about a workspace member
class MemberResponse(BaseModel):
    workspace_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
