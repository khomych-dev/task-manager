from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(100), nullable=False)
    avatar_url = Column(Text, nullable=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    google_id = Column(String(100), unique=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    owned_workspaces = relationship(
        "Workspace", back_populates="owner", cascade="all, delete-orphan"
    )
    workspace_memberships = relationship(
        "WorkspaceMember", back_populates="user", cascade="all, delete-orphan"
    )
    tasks_created = relationship(
        "Task", foreign_keys="[Task.creator_id]", back_populates="creator"
    )
    tasks_assigned = relationship(
        "Task", foreign_keys="[Task.assignee_id]", back_populates="assignee"
    )
    comments = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )
