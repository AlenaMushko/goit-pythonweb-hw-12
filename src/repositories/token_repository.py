from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.token_model import TokenModel, TokenType


class TokenRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    @staticmethod
    def _to_naive_utc(value: datetime) -> datetime:
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
        stmt = select(TokenModel).where(
            TokenModel.token == token,
            TokenModel.token_type == token_type,
            TokenModel.expires_at > datetime.utcnow(),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_token(self, token: TokenModel) -> None:
        await self.db.delete(token)
        await self.db.commit()

    async def delete_user_tokens_by_type(self, user_id: int, token_type: TokenType) -> None:
        stmt = delete(TokenModel).where(
            TokenModel.user_id == user_id,
            TokenModel.token_type == token_type,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def cleanup_expired_tokens(self) -> int:
        stmt = delete(TokenModel).where(TokenModel.expires_at <= datetime.utcnow())
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount or 0
