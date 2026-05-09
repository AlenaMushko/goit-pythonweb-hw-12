"""Unit tests for token cleanup job."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest


class _FakeSessionManager:
    def session(self):
        @asynccontextmanager
        async def _inner():
            yield AsyncMock()

        return _inner()


@pytest.mark.asyncio
async def test_cleanup_expired_tokens_once(monkeypatch):
    monkeypatch.setattr(
        "src.utils.token_cleanup.sessionmanager",
        _FakeSessionManager(),
    )

    with patch("src.utils.token_cleanup.TokenRepository") as TR:
        TR.return_value.cleanup_expired_tokens = AsyncMock(return_value=7)

        from src.utils.token_cleanup import cleanup_expired_tokens_once

        deleted = await cleanup_expired_tokens_once()

    assert deleted == 7
