"""Shared pytest fixtures."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contact_model import ContactModel
from src.models.user_model import UserModel
from src.models.user_role import UserRole


@pytest.fixture
def mock_async_session() -> AsyncMock:
    """Async SQLAlchemy session with common async methods mocked."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def sample_user() -> UserModel:
    """Regular user (non-admin) for repository and permission tests."""
    return UserModel(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password="Secret123",
        avatar=None,
        is_verified=True,
        role=UserRole.USER,
    )


@pytest.fixture
def sample_admin_user() -> UserModel:
    """Admin user; e.g. API routes that allow only UserRole.ADMIN (avatar upload)."""
    return UserModel(
        id=2,
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        password="Secret123",
        avatar="https://cdn.example/old.png",
        is_verified=True,
        role=UserRole.ADMIN,
    )


@pytest.fixture
def sample_contact(sample_user: UserModel) -> ContactModel:
    """Contact row owned by sample_user."""
    return ContactModel(
        id=10,
        name="Jane",
        surname="Smith",
        email="jane@example.com",
        phone="+380501234567",
        birthday=date(1995, 5, 15),
        additional_info=None,
        user_id=sample_user.id,
    )
