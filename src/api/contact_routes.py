from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.models.user_model import UserModel
from src.conf.constants import CONTACTS_PREFIX
from src.schemas.contact_schemas import (
    ContactBirthdayResponse,
    ContactCreate,
    ContactResponse,
    ContactUpdate,
)
from src.services.auth_service import get_current_user
from src.services.contact_service import ContactService

router = APIRouter(prefix=CONTACTS_PREFIX, tags=["contacts"])


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.create_contact(body, current_user)


@router.get("/", response_model=list[ContactResponse])
async def get_all_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: str | None = Query(default=None),
    surname: str | None = Query(default=None),
    email: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ContactService(db)

    if name or surname or email:
        return await service.search_contacts_by_query(
            name=name, surname=surname, email=email, user=current_user, skip=skip, limit=limit
        )

    return await service.get_all_contacts(user=current_user, skip=skip, limit=limit)


@router.get("/birthdays/upcoming", response_model=list[ContactBirthdayResponse])
async def get_upcoming_birthdays(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.get_upcoming_birthdays(user=current_user, days=days)


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact_by_id(
    contact_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.get_contact_by_id(contact_id, current_user)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    body: ContactUpdate,
    contact_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.update_contact(contact_id, body, current_user)


@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(
    contact_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.remove_contact(contact_id, current_user)
