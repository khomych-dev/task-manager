from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    user_repo = UserRepository(session)
    return AuthService(user_repo)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    obj_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Register a new user."""
    return await auth_service.register(obj_in)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate user and return tokens."""
    # OAuth2PasswordRequestForm expects the field username, we map it to our email
    obj_in = LoginRequest(email=form_data.username, password=form_data.password)
    return await auth_service.login(obj_in)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    obj_in: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Refresh access and refresh tokens."""
    return await auth_service.refresh(obj_in.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    obj_in: RefreshRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """Invalidate the refresh token."""
    await auth_service.logout(obj_in.refresh_token)
