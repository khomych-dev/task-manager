from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


# A basic diagram with fields that are common to various situations
class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True


# Registration schema (accepts open password from client)
class UserCreate(UserBase):
    password: str


# Schema for returning data through API (without password!)
class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    # This is a very important setting! It allows Pydantic to read data
    # not only from dictionaries, but also directly from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)
