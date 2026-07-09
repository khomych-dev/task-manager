import datetime
import json
from uuid import UUID

import jwt
import structlog
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate

logger = structlog.get_logger()


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register(self, obj_in: UserCreate) -> User:
        """Register a new user."""
        existing_user = await self.user_repo.get_by_email(obj_in.email)
        if existing_user:
            logger.warning(
                "registration_failed", reason="email_exists", email=obj_in.email
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        user_data = obj_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = get_password_hash(obj_in.password)

        user = await self.user_repo.create(user_data)
        logger.info("user_registered", user_id=str(user.id), email=user.email)
        return user

    async def login(self, obj_in: LoginRequest) -> TokenResponse:
        """Authenticate user and return tokens."""
        user = await self.user_repo.get_by_email(obj_in.email)
        if not user or not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not verify_password(obj_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        return await self._generate_tokens_and_save(user.id)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Issue new tokens using a valid refresh token."""
        try:
            payload = jwt.decode(
                refresh_token, settings.secret_key, algorithms=[settings.algorithm]
            )
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise ValueError("Missing subject")
            user_id = UUID(user_id_str)
        except (jwt.PyJWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        redis_key = f"refresh_token:{user_id}"
        stored_data = await redis_client.get(redis_key)
        if not stored_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked or expired",
            )

        return await self._generate_tokens_and_save(user_id)

    async def logout(self, refresh_token: str) -> None:
        """Invalidate the refresh token."""
        try:
            payload = jwt.decode(
                refresh_token, settings.secret_key, algorithms=[settings.algorithm]
            )
            user_id_str = payload.get("sub")
            if user_id_str:
                redis_key = f"refresh_token:{user_id_str}"
                await redis_client.delete(redis_key)
                logger.info("user_logged_out", user_id=user_id_str)
        except jwt.PyJWTError:
            pass  # Token is already invalid, nothing to revoke

    async def _generate_tokens_and_save(self, user_id: UUID) -> TokenResponse:
        """Helper to generate tokens and store refresh token in Redis."""
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)

        redis_key = f"refresh_token:{user_id}"
        token_data = {
            "user_id": str(user_id),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        # Save to Redis with TTL
        await redis_client.setex(
            redis_key,
            datetime.timedelta(days=settings.refresh_token_expire_days),
            json.dumps(token_data),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
