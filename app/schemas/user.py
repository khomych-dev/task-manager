from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    email: str = Field(..., pattern=r"^\S+@\S+\.\S+$")
    full_name: str = Field(..., min_length=1, max_length=100)
    avatar_url: str | None = None
    telegram_id: int | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=100)
    avatar_url: str | None = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    google_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
