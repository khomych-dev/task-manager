import datetime
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def get_password_hash(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed one."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(subject: str | Any) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> str:
    """Create a long-lived JWT refresh token."""
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt
