"""Tests for UserRepository."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models.user_role import UserRole
from src.repositories.user_repository import UserRepository
from src.schemas.user_schemas import UserCreate

_FAKE_HASH = "Aa1bbbbbbbb"


@pytest.mark.asyncio
async def test_create_user_adds_commit_refresh(mock_async_session: AsyncMock):
    body = UserCreate(
        first_name="Ann",
        last_name="Bee",
        email="ann@example.com",
        password="Secret123",
        role=UserRole.USER,
    )
    repo = UserRepository(mock_async_session)

    user = await repo.create_user(body, _FAKE_HASH, "https://avatar.example/a.png")

    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()
    added = mock_async_session.add.call_args[0][0]
    assert added.first_name == "Ann"
    assert added.email == "ann@example.com"
    assert added.password == _FAKE_HASH
    assert added.avatar == "https://avatar.example/a.png"
    assert added.role == UserRole.USER
    assert user is added


@pytest.mark.asyncio
async def test_get_user_by_email_executes_scalar(mock_async_session: AsyncMock, sample_user):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = sample_user
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = UserRepository(mock_async_session)
    found = await repo.get_user_by_email("john@example.com")

    assert found is sample_user
    mock_async_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_by_id_executes_scalar(mock_async_session: AsyncMock, sample_user):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = sample_user
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = UserRepository(mock_async_session)
    found = await repo.get_user_by_id(1)

    assert found is sample_user


@pytest.mark.asyncio
async def test_get_user_by_email_returns_none_when_not_found(mock_async_session: AsyncMock):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = UserRepository(mock_async_session)
    assert await repo.get_user_by_email("missing@example.com") is None


@pytest.mark.asyncio
async def test_get_user_by_id_returns_none_when_not_found(mock_async_session: AsyncMock):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = UserRepository(mock_async_session)
    assert await repo.get_user_by_id(999) is None


@pytest.mark.asyncio
async def test_create_user_propagates_database_error(mock_async_session: AsyncMock):
    body = UserCreate(
        first_name="Ann",
        last_name="Bee",
        email="ann@example.com",
        password="Secret123",
        role=UserRole.USER,
    )
    mock_async_session.commit = AsyncMock(side_effect=SQLAlchemyError("commit failed"))
    repo = UserRepository(mock_async_session)

    with pytest.raises(SQLAlchemyError):
        await repo.create_user(body, _FAKE_HASH, None)

    mock_async_session.refresh.assert_not_awaited()


@pytest.mark.asyncio
@patch("src.repositories.user_repository.delete_user_cache", new_callable=AsyncMock)
async def test_update_avatar_commits_and_invalidates_cache(
    delete_cache: AsyncMock, mock_async_session: AsyncMock, sample_user
):
    repo = UserRepository(mock_async_session)

    updated = await repo.update_avatar(sample_user, "https://new.avatar/img.png")

    assert updated.avatar == "https://new.avatar/img.png"
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()
    delete_cache.assert_awaited_once_with(sample_user.email)


@pytest.mark.asyncio
@patch("src.repositories.user_repository.delete_user_cache", new_callable=AsyncMock)
async def test_update_password_commits_and_invalidates_cache(
    delete_cache: AsyncMock, mock_async_session: AsyncMock, sample_user
):
    repo = UserRepository(mock_async_session)

    updated = await repo.update_password(sample_user, "Aa1newhashhh")

    assert updated.password == "Aa1newhashhh"
    delete_cache.assert_awaited_once_with(sample_user.email)


@pytest.mark.asyncio
@patch("src.repositories.user_repository.delete_user_cache", new_callable=AsyncMock)
async def test_update_avatar_does_not_invalidate_cache_when_commit_fails(
    delete_cache: AsyncMock, mock_async_session: AsyncMock, sample_user
):
    mock_async_session.commit = AsyncMock(side_effect=SQLAlchemyError("commit failed"))
    repo = UserRepository(mock_async_session)

    with pytest.raises(SQLAlchemyError):
        await repo.update_avatar(sample_user, "https://fail.example/a.png")

    mock_async_session.refresh.assert_not_awaited()
    delete_cache.assert_not_awaited()


@pytest.mark.asyncio
@patch("src.repositories.user_repository.delete_user_cache", new_callable=AsyncMock)
async def test_update_password_does_not_invalidate_cache_when_commit_fails(
    delete_cache: AsyncMock, mock_async_session: AsyncMock, sample_user
):
    mock_async_session.commit = AsyncMock(side_effect=SQLAlchemyError("commit failed"))
    repo = UserRepository(mock_async_session)

    with pytest.raises(SQLAlchemyError):
        await repo.update_password(sample_user, "Aa1newhashhh")

    delete_cache.assert_not_awaited()
