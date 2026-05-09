"""Unit tests for Redis-oriented user cache schemas."""

from src.models.user_model import UserModel
from src.models.user_role import UserRole
from src.schemas.current_user import CurrentUser, current_user_from_cache, user_to_cache_payload


def test_user_to_cache_payload_omits_password(sample_user: UserModel):
    payload = user_to_cache_payload(sample_user)
    assert "password" not in payload
    assert payload["email"] == sample_user.email
    assert payload["role"] == UserRole.USER.value


def test_current_user_from_cache_roundtrip(sample_user: UserModel):
    payload = user_to_cache_payload(sample_user)
    parsed = current_user_from_cache(payload)
    assert isinstance(parsed, CurrentUser)
    assert parsed.email == sample_user.email


def test_current_user_from_cache_invalid_returns_none():
    assert current_user_from_cache({}) is None
