import datetime
import json
from uuid import UUID

import structlog
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import create_access_token, create_refresh_token
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse

logger = structlog.get_logger()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


class GoogleOAuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def generate_auth_url(self, request: Request) -> str:
        """Generate Google OAuth login URL."""
        redirect_uri = settings.google_redirect_uri
        url = await oauth.google.create_authorization_url(request, redirect_uri)
        return str(url)

    async def auth_callback(self, request: Request) -> TokenResponse:
        """Process Google OAuth callback and return tokens."""
        try:
            token = await oauth.google.authorize_access_token(request)
        except Exception as e:
            logger.error("oauth_callback_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not validate credentials from Google",
            )

        user_info = token.get("userinfo")
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing user info from Google",
            )

        email = user_info.get("email")
        google_id = user_info.get("sub")
        full_name = user_info.get("name")
        avatar_url = user_info.get("picture")

        if not email or not google_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incomplete user info from Google",
            )

        user = await self.user_repo.get_by_email(email)

        if user:
            if not user.google_id:
                update_data = {"google_id": google_id, "avatar_url": avatar_url}
                user = await self.user_repo.update(user, update_data)
                logger.info("google_account_linked", user_id=str(user.id))
        else:
            create_data = {
                "email": email,
                "full_name": full_name or email.split("@")[0],
                "google_id": google_id,
                "avatar_url": avatar_url,
            }
            user = await self.user_repo.create(create_data)
            logger.info("user_registered_via_google", user_id=str(user.id))

        return await self._generate_tokens_and_save(user.id)

    async def _generate_tokens_and_save(self, user_id: UUID) -> TokenResponse:
        """Helper to generate tokens and store refresh token in Redis."""
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)

        redis_key = f"refresh_token:{user_id}"
        token_data = {
            "user_id": str(user_id),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        await redis_client.setex(
            redis_key,
            datetime.timedelta(days=settings.refresh_token_expire_days),
            json.dumps(token_data),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
