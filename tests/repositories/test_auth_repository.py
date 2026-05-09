"""Tests for AuthRepository."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.auth_repository import AuthRepository


@pytest.mark.asyncio
async def test_confirm_email_sets_verified_and_commits(sample_user, mock_async_session: AsyncMock):
    repo = AuthRepository(mock_async_session)

    await repo.confirm_email(sample_user)

    assert sample_user.is_verified is True
    mock_async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_email_propagates_when_commit_fails(sample_user, mock_async_session: AsyncMock):
    mock_async_session.commit = AsyncMock(side_effect=SQLAlchemyError("commit failed"))
    repo = AuthRepository(mock_async_session)

    with pytest.raises(SQLAlchemyError):
        await repo.confirm_email(sample_user)

    assert sample_user.is_verified is True
