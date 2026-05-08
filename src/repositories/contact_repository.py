from datetime import date

from sqlalchemy import and_, extract, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contact_model import ContactModel
from src.models.user_model import UserModel
from src.schemas.contact_schemas import ContactCreate, ContactUpdate


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_contact(self, body: ContactCreate, user: UserModel) -> ContactModel:
        contact = ContactModel(**body.model_dump(), user_id=user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def get_all_contacts(
        self, user: UserModel, skip: int = 0, limit: int = 100
    ) -> list[ContactModel]:
        stmt = select(ContactModel).where(ContactModel.user_id == user.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_contact_by_id(self, contact_id: int, user: UserModel) -> ContactModel | None:
        stmt = select(ContactModel).where(
            ContactModel.id == contact_id, ContactModel.user_id == user.id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: UserModel
    ) -> ContactModel | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: UserModel) -> ContactModel | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contacts_by_query(
        self,
        name: str | None = None,
        surname: str | None = None,
        email: str | None = None,
        user: UserModel | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ContactModel]:
        filters = []
        if name:
            filters.append(ContactModel.name.ilike(f"%{name}%"))
        if surname:
            filters.append(ContactModel.surname.ilike(f"%{surname}%"))
        if email:
            filters.append(ContactModel.email.ilike(f"%{email}%"))

        stmt = select(ContactModel)
        if user is not None:
            stmt = stmt.where(ContactModel.user_id == user.id)
        if filters:
            stmt = stmt.where(or_(*filters))

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming_birthdays(
        self, _start_date: date, _end_date: date, user: UserModel
    ) -> list[ContactModel]:
        start_md = _start_date.month * 100 + _start_date.day
        end_md = _end_date.month * 100 + _end_date.day
        birthday_md = extract("month", ContactModel.birthday) * 100 + extract(
            "day", ContactModel.birthday
        )

        if start_md <= end_md:
            date_filter = and_(birthday_md >= start_md, birthday_md <= end_md)
        else:
            date_filter = or_(birthday_md >= start_md, birthday_md <= end_md)

        stmt = select(ContactModel).where(date_filter, ContactModel.user_id == user.id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
