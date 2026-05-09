"""Unit tests for Redis cache helpers (client mocked)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.services.redis_service as redis_service


@pytest.fixture(autouse=True)
def reset_redis_singleton():
    redis_service.redis_client = None
    yield
    redis_service.redis_client = None


@pytest.mark.asyncio
async def test_init_redis_failure_sets_client_none():
    with patch("src.services.redis_service.Redis") as R:
        R.from_url.return_value.ping = AsyncMock(side_effect=RuntimeError("no redis"))
        await redis_service.init_redis()
        assert redis_service.redis_client is None


@pytest.mark.asyncio
async def test_get_user_cache_returns_none_when_client_disabled(monkeypatch):
    monkeypatch.setattr(redis_service, "redis_client", None)
    assert await redis_service.get_user_cache("any@example.com") is None


@pytest.mark.asyncio
async def test_set_user_cache_noop_when_client_disabled(monkeypatch):
    monkeypatch.setattr(redis_service, "redis_client", None)
    await redis_service.set_user_cache("any@example.com", {"id": 1})


@pytest.mark.asyncio
async def test_delete_user_cache_noop_when_client_disabled(monkeypatch):
    monkeypatch.setattr(redis_service, "redis_client", None)
    await redis_service.delete_user_cache("any@example.com")


@pytest.mark.asyncio
async def test_close_redis_when_none(monkeypatch):
    monkeypatch.setattr(redis_service, "redis_client", None)
    await redis_service.close_redis()
    assert redis_service.redis_client is None


@pytest.mark.asyncio
async def test_close_redis_aclose_called(monkeypatch):
    client = MagicMock()
    client.aclose = AsyncMock()
    monkeypatch.setattr(redis_service, "redis_client", client)

    await redis_service.close_redis()

    client.aclose.assert_awaited_once()
    assert redis_service.redis_client is None
