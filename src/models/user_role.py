from enum import Enum


class UserRole(str, Enum):
    """Available authorization roles for users."""
    USER = "user"
    ADMIN = "admin"
