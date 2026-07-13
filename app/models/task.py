from sqlalchemy import Column, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="todo", nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)

    assignee_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    creator_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )

    tags = Column(ARRAY(Text), server_default="{}")

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    creator = relationship(
        "User", foreign_keys=[creator_id], back_populates="tasks_created"
    )
    assignee = relationship(
        "User", foreign_keys=[assignee_id], back_populates="tasks_assigned"
    )
    workspace = relationship("Workspace", back_populates="tasks")
    comments = relationship(
        "Comment", back_populates="task", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    text = Column(Text, nullable=False)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    author_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")
