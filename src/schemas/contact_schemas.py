from datetime import date
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.conf.constants import (
    ADDITIONAL_INFO_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    EMAIL_REGEX,
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    PHONE_REGEX,
)


class ContactBase(BaseModel):
    """Base schema for creating and returning contact data."""
    name: str = Field(min_length=3, max_length=NAME_MAX_LENGTH)
    surname: str = Field(min_length=3, max_length=NAME_MAX_LENGTH)
    email: str = Field(max_length=EMAIL_MAX_LENGTH)
    phone: str = Field(max_length=PHONE_MAX_LENGTH)
    birthday: date
    additional_info: str | None = Field(default=None, max_length=ADDITIONAL_INFO_MAX_LENGTH)

    @field_validator("name", "surname", "email", "phone", "additional_info", mode="before")
    @classmethod
    def trim_string_fields(cls, value):
        """Trim strings and normalize empty values to None."""
        if isinstance(value, str):
            value = value.strip()
            return value if value != "" else None
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate required contact email field."""
        if not value:
            raise ValueError("Email is required")
        if not re.match(EMAIL_REGEX, value):
            raise ValueError("Invalid email format")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """Validate required contact phone field."""
        if not value:
            raise ValueError("Phone is required")
        if not re.match(PHONE_REGEX, value):
            raise ValueError("Invalid phone format")
        return value

    @field_validator("name", "surname")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """Validate required textual fields."""
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, value: date) -> date:
        """Validate that birthday is not in the future."""
        if value > date.today():
            raise ValueError("Birthday cannot be in the future")
        return value


class ContactCreate(ContactBase):
    """Schema for contact creation payload."""
    pass


class ContactUpdate(BaseModel):
    """Schema for partial update of existing contact."""
    name: str | None = Field(default=None, min_length=1, max_length=NAME_MAX_LENGTH)
    surname: str | None = Field(default=None, min_length=1, max_length=NAME_MAX_LENGTH)
    email: str | None = Field(default=None, max_length=EMAIL_MAX_LENGTH)
    phone: str | None = Field(default=None, max_length=PHONE_MAX_LENGTH)
    birthday: date | None = None
    additional_info: str | None = Field(default=None, max_length=ADDITIONAL_INFO_MAX_LENGTH)

    @field_validator("name", "surname", "email", "phone", "additional_info", mode="before")
    @classmethod
    def trim_optional_string_fields(cls, value):
        """Trim optional strings and normalize blanks to None."""
        if isinstance(value, str):
            value = value.strip()
            return value if value != "" else None
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        """Validate optional email value format."""
        if value is not None and not re.match(EMAIL_REGEX, value):
            raise ValueError("Invalid email format")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Validate optional phone value format."""
        if value is not None and not re.match(PHONE_REGEX, value):
            raise ValueError("Invalid phone format")
        return value

    @field_validator("name", "surname")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        """Return optional text fields as-is after trim step."""
        return value

    @field_validator("birthday")
    @classmethod
    def validate_optional_birthday(cls, value: date | None) -> date | None:
        """Validate optional birthday value when provided."""
        if value is not None and value > date.today():
            raise ValueError("Birthday cannot be in the future")
        return value

    @model_validator(mode="after")
    def validate_not_empty_payload(self):
        """Ensure update payload contains at least one meaningful field."""
        payload = self.model_dump(exclude_unset=True)
        if not payload:
            raise ValueError("At least one field must be provided for update")

        required_non_empty_fields = ("name", "surname", "email", "phone")
        for field_name in required_non_empty_fields:
            if field_name in payload and payload[field_name] is None:
                raise ValueError(f"{field_name.capitalize()} cannot be empty")

        if "birthday" in payload and payload["birthday"] is None:
            raise ValueError("Birthday cannot be empty")

        return self


class ContactResponse(ContactBase):
    """Schema returned for contact API responses."""
    id: int

    model_config = ConfigDict(from_attributes=True)


class ContactBirthdayResponse(BaseModel):
    """Schema for upcoming birthday response item."""
    name: str
    surname: str
    congratulation_date: date
