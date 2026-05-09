"""Unit tests for ContactService error paths."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from src.models.user_model import UserModel
from src.models.user_role import UserRole
from src.services.contact_service import ContactService


@pytest.fixture
def user(sample_user: UserModel) -> UserModel:
    return sample_user


@pytest.mark.asyncio
async def test_get_contact_by_id_raises_404(mock_async_session: AsyncMock, user: UserModel):
    service = ContactService(mock_async_session)
    service.repository.get_contact_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.get_contact_by_id(99, user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_contact_delegates_to_repository(mock_async_session: AsyncMock, user: UserModel):
    from datetime import date

    from src.models.contact_model import ContactModel
    from src.schemas.contact_schemas import ContactCreate

    body = ContactCreate(
        name="Tom",
        surname="Lee",
        email="tom@example.com",
        phone="+380503333333",
        birthday=date(1991, 1, 1),
    )
    created = ContactModel(
        id=3,
        name=body.name,
        surname=body.surname,
        email=body.email,
        phone=body.phone,
        birthday=body.birthday,
        user_id=user.id,
    )

    service = ContactService(mock_async_session)
    service.repository.create_contact = AsyncMock(return_value=created)

    with patch.object(service.logger, "info"):
        result = await service.create_contact(body, user)

    assert result.id == 3
    service.repository.create_contact.assert_awaited_once_with(body, user)
