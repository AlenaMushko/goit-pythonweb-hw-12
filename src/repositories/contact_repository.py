from datetime import date

from sqlalchemy import and_, extract, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contact_model import ContactModel
from src.models.user_model import UserModel
from src.schemas.contact_schemas import ContactCreate, ContactUpdate


class ContactRepository:
    """Data access layer for contact entities."""
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Active asynchronous SQLAlchemy session.
        """
        self.db = session

    async def create_contact(self, body: ContactCreate, user: UserModel) -> ContactModel:
        """
        Create and persist a contact.

        Args:
            body: Contact creation payload.
            user: Owner of the contact.

        Returns:
            Created contact model.
        """
        contact = ContactModel(**body.model_dump(), user_id=user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def get_all_contacts(
        self, user: UserModel, skip: int = 0, limit: int = 100
    ) -> list[ContactModel]:
        """
        Get paginated list of contacts for a user.

        Args:
            user: Owner of contacts.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of contact models.
        """
        stmt = select(ContactModel).where(ContactModel.user_id == user.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_contact_by_id(self, contact_id: int, user: UserModel) -> ContactModel | None:
        """
        Get a contact by identifier.

        Args:
            contact_id: Contact identifier.
            user: Owner of the contact.

        Returns:
            Contact model or None.
        """
        stmt = select(ContactModel).where(
            ContactModel.id == contact_id, ContactModel.user_id == user.id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: UserModel
    ) -> ContactModel | None:
        """
        Update contact fields and persist changes.

        Args:
            contact_id: Contact identifier.
            body: Partial contact update payload.
            user: Owner of the contact.

        Returns:
            Updated contact model or None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: UserModel) -> ContactModel | None:
        """
        Delete contact by identifier.

        Args:
            contact_id: Contact identifier.
            user: Owner of the contact.

        Returns:
            Deleted contact model or None.
        """
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
        """
        Search contacts using optional text filters.

        Args:
            name: Optional name filter.
            surname: Optional surname filter.
            email: Optional email filter.
            user: Optional owner filter.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of matching contacts.
        """
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
        """
        Get contacts with birthdays in requested date interval.

        Args:
            _start_date: Interval start date.
            _end_date: Interval end date.
            user: Owner of contacts.

        Returns:
            List of contacts with birthdays in interval.
        """
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
