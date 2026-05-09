"""Tests for TokenRepository."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models.token_model import TokenModel, TokenType
from src.repositories.token_repository import TokenRepository


def test_to_naive_utc_keeps_naive():
    naive = datetime(2026, 1, 1, 12, 0, 0)
    assert TokenRepository._to_naive_utc(naive) == naive


def test_to_naive_utc_converts_aware_to_naive_utc():
    aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    out = TokenRepository._to_naive_utc(aware)
    assert out.tzinfo is None
    assert out == datetime(2026, 1, 1, 12, 0, 0)


@pytest.mark.asyncio
async def test_create_token_persists_and_refreshes(mock_async_session: AsyncMock):
    repo = TokenRepository(mock_async_session)
    expires = datetime(2026, 6, 1, tzinfo=timezone.utc)

    token = await repo.create_token("jwt-value", 42, TokenType.ACCESS, expires)

    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()
    added = mock_async_session.add.call_args[0][0]
    assert isinstance(added, TokenModel)
    assert added.token == "jwt-value"
    assert added.user_id == 42
    assert added.token_type == TokenType.ACCESS
    assert token is added


@pytest.mark.asyncio
async def test_get_active_token_returns_scalar(mock_async_session: AsyncMock):
    db_token = MagicMock(spec=TokenModel)
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = db_token
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = TokenRepository(mock_async_session)
    found = await repo.get_active_token("t", TokenType.REFRESH)

    assert found is db_token


@pytest.mark.asyncio
async def test_get_active_token_returns_none_when_no_match(mock_async_session: AsyncMock):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = TokenRepository(mock_async_session)
    assert await repo.get_active_token("revoked", TokenType.ACCESS) is None


@pytest.mark.asyncio
async def test_create_token_propagates_when_commit_fails(mock_async_session: AsyncMock):
    mock_async_session.commit = AsyncMock(side_effect=SQLAlchemyError("commit failed"))
    repo = TokenRepository(mock_async_session)
    expires = datetime(2026, 6, 1, tzinfo=timezone.utc)

    with pytest.raises(SQLAlchemyError):
        await repo.create_token("jwt", 1, TokenType.ACCESS, expires)

    mock_async_session.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_token_propagates_when_commit_fails(mock_async_session: AsyncMock):
    mock_async_session.commit = AsyncMock(side_effect=SQLAlchemyError("commit failed"))
    repo = TokenRepository(mock_async_session)

    with pytest.raises(SQLAlchemyError):
        await repo.delete_token(MagicMock(spec=TokenModel))


@pytest.mark.asyncio
async def test_delete_token_deletes_and_commits(mock_async_session: AsyncMock):
    repo = TokenRepository(mock_async_session)
    token = MagicMock(spec=TokenModel)

    await repo.delete_token(token)

    mock_async_session.delete.assert_awaited_once_with(token)
    mock_async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_user_tokens_by_type_executes_delete(mock_async_session: AsyncMock):
    repo = TokenRepository(mock_async_session)

    await repo.delete_user_tokens_by_type(7, TokenType.ACCESS)

    mock_async_session.execute.assert_awaited_once()
    mock_async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanup_expired_tokens_returns_rowcount(mock_async_session: AsyncMock):
    result_mock = MagicMock()
    result_mock.rowcount = 3
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = TokenRepository(mock_async_session)
    deleted = await repo.cleanup_expired_tokens()

    assert deleted == 3


@pytest.mark.asyncio
async def test_cleanup_expired_tokens_none_rowcount_becomes_zero(mock_async_session: AsyncMock):
    result_mock = MagicMock()
    result_mock.rowcount = None
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = TokenRepository(mock_async_session)
    deleted = await repo.cleanup_expired_tokens()

    assert deleted == 0
