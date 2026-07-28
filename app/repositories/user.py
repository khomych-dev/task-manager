from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=User, session=session)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(
            select(self.model).filter(self.model.email == email)
        )
        return result.scalars().first()

    async def get_users_by_emails(self, emails: list[str]) -> Sequence[User]:
        """Get users by a list of emails."""
        if not emails:
            return []
        result = await self.session.execute(
            select(self.model).where(self.model.email.in_(emails))
        )
        return result.scalars().all()
