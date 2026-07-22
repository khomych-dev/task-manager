from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.repositories.user import UserRepository

# Specify the URL where Swagger UI will send a request to obtain a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Extracts the JWT token from the Authorization header,
    validates it, and returns the current User object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user_repo = UserRepository(session)
    user = await user_repo.get(user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


def require_role(min_role: str):
    """
    Dependency generator that checks if the current user has the required minimum role
    in the specified workspace.
    """

    async def role_checker(
        workspace_id: UUID,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> WorkspaceMember:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        result = await session.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this workspace",
            )

        role_hierarchy = {"viewer": 1, "member": 2, "admin": 3, "owner": 4}
        user_role_level = role_hierarchy.get(member.role, 0)
        min_role_level = role_hierarchy.get(min_role, 0)

        if user_role_level < min_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions in this workspace",
            )

        return member

    return role_checker
