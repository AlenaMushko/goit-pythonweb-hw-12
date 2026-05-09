"""Integration tests for contact CRUD/search routes."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from src.conf.constants import API_PREFIX
from src.models.contact_model import ContactModel


def _contact_body(**kwargs):
    base = {
        "name": "Alice",
        "surname": "Brown",
        "email": "alice-int@example.com",
        "phone": "+380671112233",
        "birthday": "1992-03-10",
    }
    base.update(kwargs)
    return base


@pytest.mark.usefixtures("mock_db", "override_current_user")
def test_create_contact_returns_201(client, sample_user):
    row = ContactModel(
        id=1,
        name="Alice",
        surname="Brown",
        email="alice-int@example.com",
        phone="+380671112233",
        birthday=date(1992, 3, 10),
        additional_info=None,
        user_id=sample_user.id,
    )
    with patch("src.api.contact_routes.ContactService") as Svc:
        inst = MagicMock()
        inst.create_contact = AsyncMock(return_value=row)
        Svc.return_value = inst

        response = client.post(
            f"{API_PREFIX}/contacts/",
            json=_contact_body(),
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["email"] == row.email
    inst.create_contact.assert_awaited_once()


@pytest.mark.usefixtures("mock_db", "override_current_user")
def test_get_all_contacts_without_filters(client):
    rows = []
    with patch("src.api.contact_routes.ContactService") as Svc:
        inst = MagicMock()
        inst.get_all_contacts = AsyncMock(return_value=rows)
        Svc.return_value = inst

        response = client.get(f"{API_PREFIX}/contacts/")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.usefixtures("mock_db", "override_current_user")
def test_search_contacts_with_query_params(client, sample_user):
    row = ContactModel(
        id=2,
        name="Bob",
        surname="Lee",
        email="bob@example.com",
        phone="+380501111111",
        birthday=date(1990, 1, 2),
        additional_info=None,
        user_id=sample_user.id,
    )

    with patch("src.api.contact_routes.ContactService") as Svc:
        inst = MagicMock()
        inst.search_contacts_by_query = AsyncMock(return_value=[row])
        Svc.return_value = inst

        response = client.get(
            f"{API_PREFIX}/contacts/",
            params={"name": "Bo", "skip": 0, "limit": 10},
        )

    assert response.status_code == 200
    inst.search_contacts_by_query.assert_awaited_once()


@pytest.mark.usefixtures("mock_db", "override_current_user")
def test_get_contact_by_id(client):
    row = ContactModel(
        id=5,
        name="Zoe",
        surname="Lee",
        email="zoe@example.com",
        phone="+380502222222",
        birthday=date(1988, 7, 7),
        additional_info=None,
        user_id=1,
    )
    with patch("src.api.contact_routes.ContactService") as Svc:
        inst = MagicMock()
        inst.get_contact_by_id = AsyncMock(return_value=row)
        Svc.return_value = inst

        response = client.get(f"{API_PREFIX}/contacts/5")

    assert response.status_code == 200
    assert response.json()["id"] == 5


@pytest.mark.usefixtures("mock_db", "override_current_user")
def test_update_contact(client):
    row = ContactModel(
        id=5,
        name="Zoe",
        surname="Lee",
        email="zoe@example.com",
        phone="+380502222222",
        birthday=date(1988, 7, 7),
        additional_info=None,
        user_id=1,
    )
    with patch("src.api.contact_routes.ContactService") as Svc:
        inst = MagicMock()
        inst.update_contact = AsyncMock(return_value=row)
        Svc.return_value = inst

        response = client.patch(
            f"{API_PREFIX}/contacts/5",
            json={"name": "Zoe2"},
        )

    assert response.status_code == 200


@pytest.mark.usefixtures("mock_db", "override_current_user")
def test_remove_contact(client):
    row = ContactModel(
        id=5,
        name="Zoe",
        surname="Lee",
        email="zoe@example.com",
        phone="+380502222222",
        birthday=date(1988, 7, 7),
        additional_info=None,
        user_id=1,
    )
    with patch("src.api.contact_routes.ContactService") as Svc:
        inst = MagicMock()
        inst.remove_contact = AsyncMock(return_value=row)
        Svc.return_value = inst

        response = client.delete(f"{API_PREFIX}/contacts/5")

    assert response.status_code == 200


@pytest.mark.usefixtures("mock_db", "override_current_user")
def test_upcoming_birthdays(client):
    with patch("src.api.contact_routes.ContactService") as Svc:
        inst = MagicMock()
        inst.get_upcoming_birthdays = AsyncMock(return_value=[])
        Svc.return_value = inst

        response = client.get(
            f"{API_PREFIX}/contacts/birthdays/upcoming",
            params={"days": 14},
        )

    assert response.status_code == 200
    assert response.json() == []
