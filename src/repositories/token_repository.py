from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.token_model import TokenModel, TokenType


class TokenRepository:
    """Data access layer for persisted authentication tokens."""
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Active asynchronous SQLAlchemy session.
        """
        self.db = session

    @staticmethod
    def _to_naive_utc(value: datetime) -> datetime:
        """
        Normalize datetime value to naive UTC format.

        Args:
            value: Datetime to normalize.

        Returns:
            Naive UTC datetime.
        """
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    async def create_token(
        self,
        token: str,
        user_id: int,
        token_type: TokenType,
        expires_at: datetime,
    ) -> TokenModel:
        """
        Persist token with metadata and expiration.

        Args:
            token: Encoded token string.
            user_id: Owner user identifier.
            token_type: Token category.
            expires_at: Expiration datetime.

        Returns:
            Persisted token model.
        """
        db_token = TokenModel(
            token=token,
            user_id=user_id,
            token_type=token_type,
            expires_at=self._to_naive_utc(expires_at),
        )
        self.db.add(db_token)
        await self.db.commit()
        await self.db.refresh(db_token)
        return db_token

    async def get_active_token(self, token: str, token_type: TokenType) -> TokenModel | None:
        """
        Get non-expired token by value and type.

        Args:
            token: Encoded token string.
            token_type: Expected token category.

        Returns:
            Active token model or None.
        """
        stmt = select(TokenModel).where(
            TokenModel.token == token,
            TokenModel.token_type == token_type,
            TokenModel.expires_at > datetime.utcnow(),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_token(self, token: TokenModel) -> None:
        """
        Delete token record.

        Args:
            token: Token model to delete.
        """
        await self.db.delete(token)
        await self.db.commit()

    async def delete_user_tokens_by_type(self, user_id: int, token_type: TokenType) -> None:
        """
        Delete all user tokens of the selected type.

        Args:
            user_id: User identifier.
            token_type: Token category to delete.
        """
        stmt = delete(TokenModel).where(
            TokenModel.user_id == user_id,
            TokenModel.token_type == token_type,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def cleanup_expired_tokens(self) -> int:
        """
        Delete all expired tokens.

        Returns:
            Number of deleted token rows.
        """
        stmt = delete(TokenModel).where(TokenModel.expires_at <= datetime.utcnow())
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount or 0
