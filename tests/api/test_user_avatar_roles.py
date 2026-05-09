"""Role checks for PATCH /users/avatar (only admins may upload)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import user_routes
from src.conf.constants import API_PREFIX
from src.db.session import get_db
from src.models.user_model import UserModel
from src.models.user_role import UserRole
from src.services.auth_service import get_current_user


@pytest.fixture
def users_app() -> FastAPI:
    """App slice with user routes only (no Redis lifespan from main)."""
    app = FastAPI()
    app.include_router(user_routes.router, prefix=API_PREFIX)
    return app


@pytest.fixture
def client(users_app: FastAPI) -> TestClient:
    return TestClient(users_app)


@pytest.fixture
def override_db(users_app: FastAPI):
    async def _db() -> AsyncMock:
        session = AsyncMock(spec=AsyncSession)
        yield session

    users_app.dependency_overrides[get_db] = _db
    yield
    users_app.dependency_overrides.pop(get_db, None)


def test_update_avatar_forbidden_for_regular_user(client: TestClient, users_app: FastAPI, sample_user: UserModel):
    async def _user() -> UserModel:
        return sample_user

    users_app.dependency_overrides[get_current_user] = _user
    try:
        response = client.patch(
            f"{API_PREFIX}/users/avatar",
            files={"file": ("a.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )
    finally:
        users_app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
    assert response.json()["detail"] == "Only admins can update avatar"


@pytest.mark.usefixtures("override_db")
def test_update_avatar_allowed_for_admin(
    client: TestClient,
    users_app: FastAPI,
    sample_admin_user: UserModel,
):
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

    async def _admin() -> UserModel:
        return sample_admin_user

    users_app.dependency_overrides[get_current_user] = _admin

    mock_instance = MagicMock()
    mock_instance.update_avatar = AsyncMock(return_value=updated)

    try:
        with patch("src.api.user_routes.UserService", return_value=mock_instance):
            response = client.patch(
                f"{API_PREFIX}/users/avatar",
                files={"file": ("a.png", b"\x89PNG\r\n\x1a\n", "image/png")},
            )
    finally:
        users_app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == sample_admin_user.email
    assert body["role"] == UserRole.ADMIN.value
    assert body["avatar"] == "https://cdn.example/new.png"
    mock_instance.update_avatar.assert_awaited_once()
