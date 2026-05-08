from datetime import date
import re

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.db.base import Base
from src.conf.constants import (
    NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    ADDITIONAL_INFO_MAX_LENGTH,
    EMAIL_REGEX,
    PHONE_REGEX,
)


class ContactModel(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("email", name="uq_contacts_email"),
        UniqueConstraint("phone", name="uq_contacts_phone"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    surname: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(PHONE_MAX_LENGTH), nullable=False, unique=True)
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    additional_info: Mapped[str | None] = mapped_column(
        String(ADDITIONAL_INFO_MAX_LENGTH), nullable=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("UserModel", back_populates="contacts")

    @validates("email")
    def validate_email(self, key, value: str) -> str:
        if not re.match(EMAIL_REGEX, value):
            raise ValueError("Invalid email format")
        return value

    @validates("phone")
    def validate_phone(self, key, value: str) -> str:
        if not re.match(PHONE_REGEX, value):
            raise ValueError("Invalid phone format")
        return value

    @validates("birthday")
    def validate_birthday(self, key, value: date) -> date:
        if value > date.today():
            raise ValueError("Birthday cannot be in the future")
        return value

    def __repr__(self) -> str:
        return f"Contact(id={self.id!r}, name={self.name!r}, email={self.email!r}, phone={self.phone!r}, birthday={self.birthday!r}, additional_info={self.additional_info!r})"
