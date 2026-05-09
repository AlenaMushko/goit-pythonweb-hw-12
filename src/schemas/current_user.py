from dataclasses import dataclass

from src.models.user_model import UserModel
from src.models.user_role import UserRole


@dataclass
class CurrentUser:
    """Lightweight user payload returned when resolved from Redis cache."""

    id: int
    email: str
    first_name: str
    last_name: str
    avatar: str | None
    is_verified: bool
    role: UserRole


def user_to_cache_payload(user: UserModel) -> dict:
    """Safe fields for Redis user cache (no password)."""
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "avatar": user.avatar,
        "is_verified": user.is_verified,
        "role": user.role.value,
    }


def current_user_from_cache(cached: dict) -> CurrentUser | None:
    """Build CurrentUser from Redis JSON dict, or None if invalid."""
    try:
        return CurrentUser(
            id=int(cached["id"]),
            email=str(cached["email"]),
            first_name=str(cached["first_name"]),
            last_name=str(cached["last_name"]),
            avatar=cached.get("avatar"),
            is_verified=bool(cached["is_verified"]),
            role=UserRole(cached["role"]),
        )
    except (KeyError, TypeError, ValueError):
        return None
