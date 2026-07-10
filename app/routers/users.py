from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/me", tags=["users"])


def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


@router.get("", response_model=UserResponse)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user profile."""
    return current_user


@router.patch("", response_model=UserResponse)
async def update_my_profile(
    obj_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Update current user profile (e.g., full_name, avatar_url)."""
    update_data = obj_in.model_dump(exclude_unset=True)
    if update_data:
        current_user = await user_repo.update(current_user, update_data)
    return current_user
