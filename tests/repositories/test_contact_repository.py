"""Tests for ContactRepository."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.contact_repository import ContactRepository
from src.schemas.contact_schemas import ContactCreate, ContactUpdate


@pytest.mark.asyncio
async def test_create_contact_adds_commit_refresh(mock_async_session: AsyncMock, sample_user):
    body = ContactCreate(
        name="Alice",
        surname="Brown",
        email="alice@example.com",
        phone="+380671112233",
        birthday=date(1992, 3, 10),
        additional_info="note",
    )
    repo = ContactRepository(mock_async_session)

    contact = await repo.create_contact(body, sample_user)

    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()
    added = mock_async_session.add.call_args[0][0]
    assert added.user_id == sample_user.id
    assert contact is added


@pytest.mark.asyncio
async def test_get_all_contacts_returns_list(mock_async_session: AsyncMock, sample_user, sample_contact):
    scalars = MagicMock()
    scalars.all.return_value = [sample_contact]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepository(mock_async_session)
    contacts = await repo.get_all_contacts(sample_user, skip=5, limit=10)

    assert contacts == [sample_contact]


@pytest.mark.asyncio
async def test_get_contact_by_id_returns_scalar(mock_async_session: AsyncMock, sample_user, sample_contact):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = sample_contact
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepository(mock_async_session)
    found = await repo.get_contact_by_id(sample_contact.id, sample_user)

    assert found is sample_contact


@pytest.mark.asyncio
async def test_get_contact_by_id_returns_none_when_missing(mock_async_session: AsyncMock, sample_user):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepository(mock_async_session)
    assert await repo.get_contact_by_id(404, sample_user) is None


@pytest.mark.asyncio
async def test_get_all_contacts_returns_empty_list(mock_async_session: AsyncMock, sample_user):
    scalars = MagicMock()
    scalars.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepository(mock_async_session)
    assert await repo.get_all_contacts(sample_user) == []


@pytest.mark.asyncio
async def test_update_contact_applies_partial_fields(mock_async_session: AsyncMock, sample_user, sample_contact):
    repo = ContactRepository(mock_async_session)
    body = ContactUpdate(name="NewName")

    with patch.object(repo, "get_contact_by_id", new=AsyncMock(return_value=sample_contact)):
        updated = await repo.update_contact(sample_contact.id, body, sample_user)

    assert updated is sample_contact
    assert sample_contact.name == "NewName"
    mock_async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_contact_returns_none_when_missing(mock_async_session: AsyncMock, sample_user):
    repo = ContactRepository(mock_async_session)
    body = ContactUpdate(name="Xyz")

    with patch.object(repo, "get_contact_by_id", new=AsyncMock(return_value=None)):
        updated = await repo.update_contact(999, body, sample_user)

    assert updated is None
    mock_async_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_contact_deletes_when_found(mock_async_session: AsyncMock, sample_user, sample_contact):
    repo = ContactRepository(mock_async_session)

    with patch.object(repo, "get_contact_by_id", new=AsyncMock(return_value=sample_contact)):
        deleted = await repo.remove_contact(sample_contact.id, sample_user)

    assert deleted is sample_contact
    mock_async_session.delete.assert_awaited_once_with(sample_contact)
    mock_async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_contact_returns_none_when_missing(mock_async_session: AsyncMock, sample_user):
    repo = ContactRepository(mock_async_session)

    with patch.object(repo, "get_contact_by_id", new=AsyncMock(return_value=None)):
        deleted = await repo.remove_contact(1, sample_user)

    assert deleted is None
    mock_async_session.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_contacts_builds_filters(mock_async_session: AsyncMock, sample_user, sample_contact):
    scalars = MagicMock()
    scalars.all.return_value = [sample_contact]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepository(mock_async_session)
    rows = await repo.search_contacts_by_query(
        name="Ja",
        surname="Sm",
        email="jane",
        user=sample_user,
        skip=0,
        limit=50,
    )

    assert rows == [sample_contact]
    mock_async_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_contacts_returns_empty_when_no_matches(mock_async_session: AsyncMock, sample_user):
    scalars = MagicMock()
    scalars.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepository(mock_async_session)
    rows = await repo.search_contacts_by_query(name="zzz", user=sample_user)

    assert rows == []


@pytest.mark.asyncio
async def test_search_contacts_without_user_or_filters(mock_async_session: AsyncMock, sample_contact):
    scalars = MagicMock()
    scalars.all.return_value = [sample_contact]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepository(mock_async_session)
    rows = await repo.search_contacts_by_query()

    assert rows == [sample_contact]


@pytest.mark.asyncio
async def test_get_upcoming_birthdays_same_year_interval(mock_async_session: AsyncMock, sample_user, sample_contact):
    scalars = MagicMock()
    scalars.all.return_value = [sample_contact]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepository(mock_async_session)
    start = date(2026, 5, 1)
    end = date(2026, 5, 31)
    rows = await repo.get_upcoming_birthdays(start, end, sample_user)

    assert rows == [sample_contact]


@pytest.mark.asyncio
async def test_get_upcoming_birthdays_wraps_year_boundary(mock_async_session: AsyncMock, sample_user, sample_contact):
    scalars = MagicMock()
    scalars.all.return_value = [sample_contact]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars
    mock_async_session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepository(mock_async_session)
    start = date(2026, 12, 20)
    end = date(2027, 1, 10)
    rows = await repo.get_upcoming_birthdays(start, end, sample_user)

    assert rows == [sample_contact]


@pytest.mark.asyncio
async def test_create_contact_propagates_when_commit_fails(mock_async_session: AsyncMock, sample_user):
    body = ContactCreate(
        name="Alice",
        surname="Brown",
        email="alice@example.com",
        phone="+380671112233",
        birthday=date(1992, 3, 10),
    )
    mock_async_session.commit = AsyncMock(side_effect=SQLAlchemyError("commit failed"))
    repo = ContactRepository(mock_async_session)

    with pytest.raises(SQLAlchemyError):
        await repo.create_contact(body, sample_user)

    mock_async_session.refresh.assert_not_awaited()
