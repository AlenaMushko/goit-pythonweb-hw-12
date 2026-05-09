"""Integration tests against the full FastAPI application (`main.app`)."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.services.auth_service import get_current_user


@pytest.fixture
def client(monkeypatch):
    """TestClient with lifespan; token cleanup loop disabled (no real DB poll)."""
    async def noop_cleanup_loop() -> None:
        return

    import main as main_module

    monkeypatch.setattr(main_module, "token_cleanup_loop", noop_cleanup_loop)

    with TestClient(main_module.app) as test_client:
        yield test_client


@pytest.fixture
def mock_db(client):
    """Single AsyncSession mock wired into ``get_db`` for the app under test."""
    session = AsyncMock(spec=AsyncSession)

    async def _get_db():
        yield session

    client.app.dependency_overrides[get_db] = _get_db
    yield session
    client.app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def override_current_user(client, sample_user):
    async def _user():
        return sample_user

    client.app.dependency_overrides[get_current_user] = _user
    yield sample_user
    client.app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def override_current_admin(client, sample_admin_user):
    async def _admin():
        return sample_admin_user

    client.app.dependency_overrides[get_current_user] = _admin
    yield sample_admin_user
    client.app.dependency_overrides.pop(get_current_user, None)
