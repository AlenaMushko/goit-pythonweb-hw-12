from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_model import UserModel


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def confirm_email(self, user: UserModel) -> None:
        user.is_verified = True
        await self.db.commit()
