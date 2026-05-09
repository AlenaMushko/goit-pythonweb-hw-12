"""Integration tests for health route."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.conf.constants import API_PREFIX


@pytest.mark.usefixtures("mock_db")
def test_healthchecker_ok(client, mock_db):
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = 1
    mock_db.execute = AsyncMock(return_value=exec_result)

    response = client.get(f"{API_PREFIX}/healthchecker")

    assert response.status_code == 200
    assert response.json() == {"message": "API is healthy"}
    mock_db.execute.assert_awaited_once()


@pytest.mark.usefixtures("mock_db")
def test_healthchecker_db_error_returns_500(client, mock_db):
    mock_db.execute = AsyncMock(side_effect=RuntimeError("connection refused"))

    response = client.get(f"{API_PREFIX}/healthchecker")

    assert response.status_code == 500
    assert response.json()["detail"] == "Error connecting to the database"


@pytest.mark.usefixtures("mock_db")
def test_healthchecker_null_scalar_returns_500(client, mock_db):
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=exec_result)

    response = client.get(f"{API_PREFIX}/healthchecker")

    assert response.status_code == 500
    assert "database" in response.json()["detail"].lower()
