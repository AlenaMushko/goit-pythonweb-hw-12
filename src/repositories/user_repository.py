from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_model import UserModel
from src.models.user_role import UserRole
from src.schemas.user_schemas import UserCreate
from src.services.redis_service import delete_user_cache


class UserRepository:
    """Data access layer for user entities."""
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Active asynchronous SQLAlchemy session.
        """
        self.db = session

    async def create_user(self, body: UserCreate, hashed_password: str, avatar: str | None) -> UserModel:
        """
        Create and persist a user record.

        Args:
            body: User registration payload.
            hashed_password: Pre-hashed password string.
            avatar: Optional avatar URL.

        Returns:
            Newly created user model.
        """
        user = UserModel(
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            password=hashed_password,
            avatar=avatar,
            role=body.role or UserRole.USER,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> UserModel | None:
        """
        Get user by email.

        Args:
            email: Email address to search.

        Returns:
            Found user model or None.
        """
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> UserModel | None:
        """
        Get user by identifier.

        Args:
            user_id: User identifier.

        Returns:
            Found user model or None.
        """
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_avatar(self, user: UserModel, avatar_url: str) -> UserModel:
        """
        Update user avatar URL and persist changes.

        Args:
            user: Target user model.
            avatar_url: New avatar URL.

        Returns:
            Updated user model.
        """
        user.avatar = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        await delete_user_cache(user.email)
        return user

    async def update_password(self, user: UserModel, hashed_password: str) -> UserModel:
        """
        Update user password hash and persist changes.

        Args:
            user: Target user model.
            hashed_password: New hashed password.

        Returns:
            Updated user model.
        """
        user.password = hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        await delete_user_cache(user.email)
        return user
