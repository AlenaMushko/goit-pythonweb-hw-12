from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_model import UserModel
from src.repositories.contact_repository import ContactRepository
from src.schemas.contact_schemas import ContactBirthdayResponse, ContactCreate, ContactUpdate
from src.utils.logger import Logger


class ContactService:
    """Business logic for contact CRUD and birthday queries."""
    def __init__(self, db: AsyncSession):
        """
        Initialize contact service dependencies.

        Args:
            db: Active asynchronous database session.
        """
        self.repository = ContactRepository(db)
        self.logger = Logger()

    async def create_contact(self, body: ContactCreate, user: UserModel):
        """
        Create contact and log creation event.

        Args:
            body: Contact creation payload.
            user: Owner of the contact.

        Returns:
            Created contact model.
        """
        contact = await self.repository.create_contact(body, user)
        self.logger.info(
            f"Contact created successfully: id={contact.id}, name={contact.name + ' ' + contact.surname}",
            title="ContactService",
        )
        return contact

    async def get_all_contacts(self, user: UserModel, skip: int = 0, limit: int = 100):
        """
        Return paginated contacts for user.

        Args:
            user: Owner of contacts.
            skip: Number of contacts to skip.
            limit: Maximum number of contacts to return.

        Returns:
            List of contact models.
        """
        return await self.repository.get_all_contacts(user, skip, limit)

    async def get_contact_by_id(self, contact_id: int, user: UserModel):
        """
        Return contact by id or raise 404.

        Args:
            contact_id: Contact identifier.
            user: Owner of the contact.

        Returns:
            Contact model.

        Raises:
            HTTPException: If contact is not found.
        """
        contact = await self.repository.get_contact_by_id(contact_id, user)
        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )
        return contact

    async def update_contact(self, contact_id: int, body: ContactUpdate, user: UserModel):
        """
        Update contact and log update event.

        Args:
            contact_id: Contact identifier.
            body: Contact update payload.
            user: Owner of the contact.

        Returns:
            Updated contact model.

        Raises:
            HTTPException: If contact is not found.
        """
        contact = await self.repository.update_contact(contact_id, body, user)
        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )
        self.logger.info(
            f"Contact updated successfully: id={contact.id}, name={contact.name + ' ' + contact.surname}",
            title="ContactService",
        )
        return contact

    async def remove_contact(self, contact_id: int, user: UserModel):
        """
        Delete contact and log delete event.

        Args:
            contact_id: Contact identifier.
            user: Owner of the contact.

        Returns:
            Deleted contact model.

        Raises:
            HTTPException: If contact is not found.
        """
        contact = await self.repository.remove_contact(contact_id, user)
        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )
        self.logger.info(
            f"Contact removed successfully: id={contact.id}, name={contact.name + ' ' + contact.surname}",
            title="ContactService",
        )
        return contact

    async def search_contacts_by_query(
        self,
        name: str | None = None,
        surname: str | None = None,
        email: str | None = None,
        user: UserModel | None = None,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        Search contacts by optional criteria.

        Args:
            name: Optional name filter.
            surname: Optional surname filter.
            email: Optional email filter.
            user: Optional owner filter.
            skip: Number of contacts to skip.
            limit: Maximum number of contacts to return.

        Returns:
            List of matching contacts.
        """
        return await self.repository.search_contacts_by_query(name, surname, email, user, skip, limit)

    async def get_upcoming_birthdays(self, user: UserModel, days: int = 7):
        """
        Return contacts with birthdays and congratulation dates.

        Args:
            user: Owner of contacts.
            days: Number of upcoming days to inspect.

        Returns:
            List of upcoming birthday response objects.
        """
        today = date.today()
        end_date = today + timedelta(days=days)
        contacts = await self.repository.get_upcoming_birthdays(today, end_date, user)

        def birthday_in_year(birth: date, year: int) -> date:
            """
            Project birthday into target year.

            Args:
                birth: Original birthday value.
                year: Target year.

            Returns:
                Normalized date for target year.
            """
            try:
                return birth.replace(year=year)
            except ValueError:
                return date(year, 2, 28)

        upcoming_birthdays: list[ContactBirthdayResponse] = []
        for contact in contacts:
            birthday_this_year = birthday_in_year(contact.birthday, today.year)
            next_birthday = (
                birthday_this_year
                if birthday_this_year >= today
                else birthday_in_year(contact.birthday, today.year + 1)
            )

            if today <= next_birthday <= end_date:
                congratulation_date = next_birthday
                if next_birthday.weekday() == 5:
                    congratulation_date = next_birthday + timedelta(days=2)
                elif next_birthday.weekday() == 6:
                    congratulation_date = next_birthday + timedelta(days=1)

                upcoming_birthdays.append(
                    ContactBirthdayResponse(
                        name=contact.name,
                        surname=contact.surname,
                        congratulation_date=congratulation_date,
                    )
                )

        return upcoming_birthdays
