import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.conf.constants import EMAIL_MAX_LENGTH, EMAIL_REGEX, NAME_MAX_LENGTH, PASSWORD_REGEX
from src.models.user_role import UserRole


class UserBase(BaseModel):
    """Base schema with common user fields and validation."""
    first_name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    last_name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    email: str = Field(max_length=EMAIL_MAX_LENGTH)

    @field_validator("first_name", "last_name", "email", mode="before")
    @classmethod
    def trim_string_fields(cls, value):
        """Trim incoming string values before validation."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_fields(cls, value: str) -> str:
        """Validate that required name field is not empty."""
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate required email field and format."""
        if not value:
            raise ValueError("Email is required")
        if not re.match(EMAIL_REGEX, value):
            raise ValueError("Invalid email format")
        return value


class UserCreate(UserBase):
    """Schema for user registration payload."""
    password: str = Field(min_length=8, max_length=255)
    role: UserRole = UserRole.USER

    @field_validator("password", mode="before")
    @classmethod
    def trim_password(cls, value):
        """Trim incoming password value."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Validate password against project password policy."""
        if not value:
            raise ValueError("Password is required")
        if not re.match(PASSWORD_REGEX, value):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one number"
            )
        return value


class UserResponse(UserBase):
    """Schema returned for user profile API responses."""
    id: int
    avatar: str | None = None
    is_verified: bool
    role: UserRole = UserRole.USER

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Token response schema for authentication endpoints."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    """Schema for login credentials."""
    email: str
    password: str


class RequestEmail(BaseModel):
    """Schema carrying email address for email-based flows."""
    email: str


class RefreshTokenRequest(BaseModel):
    """Schema for requesting token refresh."""
    refresh_token: str


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation endpoint."""
    token: str
    user_id: int
    password: str = Field(min_length=8, max_length=255)
    confirm_password: str = Field(min_length=8, max_length=255)

    @field_validator("password", "confirm_password", mode="before")
    @classmethod
    def trim_password_fields(cls, value):
        """Trim password and confirmation fields."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("password", "confirm_password")
    @classmethod
    def validate_password_fields(cls, value: str) -> str:
        """Validate password fields against password policy."""
        if not value:
            raise ValueError("Password is required")
        if not re.match(PASSWORD_REGEX, value):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one number"
            )
        return value
