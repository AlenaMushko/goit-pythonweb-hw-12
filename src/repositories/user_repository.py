from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_model import UserModel
from src.models.user_role import UserRole
from src.schemas.user_schemas import UserCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_user(self, body: UserCreate, hashed_password: str, avatar: str | None) -> UserModel:
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
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_avatar(self, user: UserModel, avatar_url: str) -> UserModel:
        user.avatar = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, user: UserModel, hashed_password: str) -> UserModel:
        user.password = hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        return user
