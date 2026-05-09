"""Integration tests for authentication routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from src.conf.constants import API_PREFIX, AUTH_PREFIX, RESET_PASSWORD_CONFIRM_PATH, RESET_PASSWORD_PATH
from src.models.user_model import UserModel
from src.models.user_role import UserRole
from src.security.passwords import get_password_hash
from src.services.auth_service import auth_service

AUTH_BASE = f"{API_PREFIX}{AUTH_PREFIX}"


def _new_user(email: str = "signup@example.com") -> UserModel:
    return UserModel(
        id=1,
        first_name="Test",
        last_name="User",
        email=email,
        password=get_password_hash("Secret123"),
        avatar=None,
        is_verified=False,
        role=UserRole.USER,
    )


@pytest.mark.usefixtures("mock_db")
def test_signup_conflict_returns_409(client):
    existing = _new_user()
    existing.is_verified = True

    with patch("src.api.auth_routes.UserRepository") as UR:
        repo = MagicMock()
        repo.get_user_by_email = AsyncMock(return_value=existing)
        UR.return_value = repo

        response = client.post(
            f"{AUTH_BASE}/signup",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": existing.email,
                "password": "Secret123",
            },
        )

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.usefixtures("mock_db")
def test_signup_success_returns_201(client):
    created = _new_user()

    with (
        patch("src.api.auth_routes.UserRepository") as UR,
        patch("src.api.auth_routes.TokenRepository") as TR,
        patch("src.api.auth_routes.send_verification_email", new_callable=AsyncMock),
    ):
        user_repo = MagicMock()
        user_repo.get_user_by_email = AsyncMock(side_effect=[None, created])
        user_repo.create_user = AsyncMock(return_value=created)
        UR.return_value = user_repo

        token_repo = MagicMock()
        token_repo.create_token = AsyncMock(return_value=MagicMock())
        TR.return_value = token_repo

        response = client.post(
            f"{AUTH_BASE}/signup",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": created.email,
                "password": "Secret123",
            },
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["email"] == created.email


@pytest.mark.usefixtures("mock_db")
def test_login_invalid_credentials(client):
    user = _new_user()
    user.is_verified = True

    with patch("src.api.auth_routes.UserRepository") as UR:
        repo = MagicMock()
        repo.get_user_by_email = AsyncMock(return_value=user)
        UR.return_value = repo

        response = client.post(
            f"{AUTH_BASE}/login",
            json={"email": user.email, "password": "WrongPass1"},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.usefixtures("mock_db")
def test_login_unverified_email(client):
    user = _new_user()
    user.is_verified = False

    with patch("src.api.auth_routes.UserRepository") as UR:
        repo = MagicMock()
        repo.get_user_by_email = AsyncMock(return_value=user)
        UR.return_value = repo

        response = client.post(
            f"{AUTH_BASE}/login",
            json={"email": user.email, "password": "Secret123"},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "verified" in response.json()["detail"].lower()


@pytest.mark.usefixtures("mock_db")
def test_login_success_returns_tokens(client):
    user = _new_user()
    user.is_verified = True

    with (
        patch("src.api.auth_routes.UserRepository") as UR,
        patch("src.api.auth_routes.TokenRepository") as TR,
        patch("src.api.auth_routes.set_user_cache", new_callable=AsyncMock),
    ):
        UR.return_value.get_user_by_email = AsyncMock(return_value=user)

        token_repo = MagicMock()
        token_repo.delete_user_tokens_by_type = AsyncMock()
        token_repo.create_token = AsyncMock(return_value=MagicMock())
        TR.return_value = token_repo

        response = client.post(
            f"{AUTH_BASE}/login",
            json={"email": user.email, "password": "Secret123"},
        )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "access_token" in body and "refresh_token" in body


@pytest.mark.usefixtures("mock_db")
def test_refresh_invalid_token(client):
    response = client.post(
        f"{AUTH_BASE}/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.usefixtures("mock_db")
def test_refresh_success(client):
    user = _new_user()
    user.is_verified = True
    refresh_token, _ = auth_service.create_refresh_token({"sub": user.email})

    with patch("src.api.auth_routes.TokenRepository") as TR, patch(
        "src.api.auth_routes.UserRepository"
    ) as UR:
        token_repo = MagicMock()
        token_repo.get_active_token = AsyncMock(return_value=MagicMock())
        token_repo.delete_token = AsyncMock()
        token_repo.delete_user_tokens_by_type = AsyncMock()
        token_repo.create_token = AsyncMock(return_value=MagicMock())
        TR.return_value = token_repo

        UR.return_value.get_user_by_email = AsyncMock(return_value=user)

        response = client.post(
            f"{AUTH_BASE}/refresh",
            json={"refresh_token": refresh_token},
        )

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


@pytest.mark.usefixtures("mock_db")
def test_confirmed_email_invalid_token(client):
    with patch("src.api.auth_routes.TokenRepository") as TR:
        TR.return_value.get_active_token = AsyncMock(return_value=None)

        response = client.get(f"{AUTH_BASE}/confirmed_email/bad-token")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.usefixtures("mock_db")
def test_confirmed_email_already_verified(client):
    user = _new_user()
    user.is_verified = True
    token_str, _ = auth_service.create_email_token({"sub": user.email})

    with patch("src.api.auth_routes.TokenRepository") as TR, patch(
        "src.api.auth_routes.UserRepository"
    ) as UR:
        TR.return_value.get_active_token = AsyncMock(return_value=MagicMock())
        UR.return_value.get_user_by_email = AsyncMock(return_value=user)
        TR.return_value.delete_token = AsyncMock()

        response = client.get(f"{AUTH_BASE}/confirmed_email/{token_str}")

    assert response.status_code == 200
    assert "already verified" in response.json()["message"].lower()


@pytest.mark.usefixtures("mock_db")
def test_request_email_verification_always_generic_message(client):
    with patch("src.api.auth_routes.UserRepository") as UR:
        UR.return_value.get_user_by_email = AsyncMock(return_value=None)

        response = client.post(
            f"{AUTH_BASE}/request_email_verification",
            json={"email": "nobody@example.com"},
        )

    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.usefixtures("mock_db")
def test_request_password_reset_sends_when_user_exists(client):
    user = _new_user()

    with (
        patch("src.api.auth_routes.UserRepository") as UR,
        patch("src.api.auth_routes.TokenRepository") as TR,
        patch("src.api.auth_routes.send_password_reset_email", new_callable=AsyncMock),
    ):
        UR.return_value.get_user_by_email = AsyncMock(return_value=user)
        token_repo = MagicMock()
        token_repo.delete_user_tokens_by_type = AsyncMock()
        token_repo.create_token = AsyncMock(return_value=MagicMock())
        TR.return_value = token_repo

        response = client.post(
            f"{AUTH_BASE}{RESET_PASSWORD_PATH}",
            json={"email": user.email},
        )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.usefixtures("mock_db")
def test_validate_password_reset_token_rejects_invalid(client):
    with patch("src.api.auth_routes.TokenRepository") as TR:
        TR.return_value.get_active_token = AsyncMock(return_value=None)

        response = client.get(f"{AUTH_BASE}{RESET_PASSWORD_PATH}/bad")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.usefixtures("mock_db")
def test_submit_password_reset_form_password_mismatch(client):
    response = client.post(
        f"{AUTH_BASE}{RESET_PASSWORD_PATH}/any-token",
        data={
            "password": "Secret123",
            "confirm_password": "Secret124",
            "user_id": "1",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.usefixtures("mock_db")
def test_confirm_password_reset_json_mismatch(client):
    response = client.post(
        f"{AUTH_BASE}{RESET_PASSWORD_CONFIRM_PATH}",
        json={
            "token": "valid-looking-token-placeholder",
            "user_id": 1,
            "password": "Secret123",
            "confirm_password": "Secret456",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
