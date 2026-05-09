from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_model import UserModel


class AuthRepository:
    """Data access helpers for authentication state changes."""
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Active asynchronous SQLAlchemy session.
        """
        self.db = session

    async def confirm_email(self, user: UserModel) -> None:
        """
        Mark user email as verified.

        Args:
            user: User model to update.
        """
        user.is_verified = True
        await self.db.commit()
