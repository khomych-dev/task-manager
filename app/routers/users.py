import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.redis import redis_client
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import TelegramConnectRequest, UserResponse, UserUpdate

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


@router.post("/telegram/connect", response_model=UserResponse)
async def connect_telegram(
    obj_in: TelegramConnectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Link Telegram account using a 6-digit code."""
    redis_key = f"telegram_connect:{obj_in.code}"
    cached_data = await redis_client.get(redis_key)

    if not cached_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code",
        )

    payload = json.loads(cached_data)
    telegram_id = payload.get("telegram_id")

    current_user = await user_repo.update(current_user, {"telegram_id": telegram_id})

    # Delete key to prevent reuse
    await redis_client.delete(redis_key)

    return current_user
