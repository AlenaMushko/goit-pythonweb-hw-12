"""Integration tests for user profile routes (including avatar role gate)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from src.conf.constants import API_PREFIX
from src.models.user_model import UserModel
from src.models.user_role import UserRole


@pytest.mark.usefixtures("override_current_user")
def test_get_me_returns_profile(client, sample_user):
    response = client.get(f"{API_PREFIX}/users/me")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["email"] == sample_user.email
    assert body["role"] == UserRole.USER.value


@pytest.mark.usefixtures("mock_db")
def test_patch_avatar_forbidden_for_regular_user(client, override_current_user):
    response = client.patch(
        f"{API_PREFIX}/users/avatar",
        files={"file": ("a.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Only admins can update avatar"


@pytest.mark.usefixtures("mock_db", "override_current_admin")
def test_patch_avatar_allowed_for_admin(client, sample_admin_user):
    updated = UserModel(
        id=sample_admin_user.id,
        first_name=sample_admin_user.first_name,
        last_name=sample_admin_user.last_name,
        email=sample_admin_user.email,
        password=sample_admin_user.password,
        avatar="https://cdn.example/new.png",
        is_verified=True,
        role=UserRole.ADMIN,
    )

    mock_instance = MagicMock()
    mock_instance.update_avatar = AsyncMock(return_value=updated)

    with patch("src.api.user_routes.UserService", return_value=mock_instance):
        response = client.patch(
            f"{API_PREFIX}/users/avatar",
            files={"file": ("a.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["role"] == UserRole.ADMIN.value
    assert body["avatar"] == "https://cdn.example/new.png"
    mock_instance.update_avatar.assert_awaited_once()
