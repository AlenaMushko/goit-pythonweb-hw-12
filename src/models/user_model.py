from datetime import datetime
import re

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.conf.constants import (
    NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    PASSWORD_REGEX,
    EMAIL_REGEX,
)
from src.db.base import Base
from src.models.user_role import UserRole


class UserModel(Base):
    """SQLAlchemy model for application users."""
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    last_name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.USER, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    contacts = relationship("ContactModel", back_populates="owner", cascade="all, delete-orphan")
    tokens = relationship("TokenModel", back_populates="owner", cascade="all, delete-orphan")

    @validates("first_name")
    def validate_first_name(self, key, value: str) -> str:
        """Validate non-empty first name."""
        if value.strip() == "":
            raise ValueError("First name cannot be empty")
        return value

    @validates("last_name")
    def validate_last_name(self, key, value: str) -> str:
        """Validate non-empty last name."""
        if value.strip() == "":
            raise ValueError("Last name cannot be empty")
        return value

    @validates("email")
    def validate_email(self, key, value: str) -> str:
        """Validate email presence and format."""
        if value.strip() == "":
            raise ValueError("Email cannot be empty")
        if not re.match(EMAIL_REGEX, value):
            raise ValueError("Invalid email address")
        return value

    @validates("password")
    def validate_password(self, key, value: str) -> str:
        """Validate password against configured regex."""
        if value.strip() == "":
            raise ValueError("Password cannot be empty")
        if not re.match(PASSWORD_REGEX, value):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one number"
            )
        return value

    def __repr__(self) -> str:
        """Return concise debug representation."""
        return f"UserModel(id={self.id}, user_name={self.first_name + ' ' + self.last_name})"
