"""Unit tests for AuthService JWT helpers (no HTTP stack)."""

import pytest
from fastapi import HTTPException
from jose import jwt

from src.conf.config import settings
from src.services.auth_service import AuthService


@pytest.fixture
def svc() -> AuthService:
    return AuthService()


def test_access_token_roundtrip(svc: AuthService):
    token, exp = svc.create_access_token({"sub": "u@example.com"})
    email = svc.decode_access_token(token)
    assert email == "u@example.com"
    assert exp.tzinfo is not None


def test_refresh_token_roundtrip(svc: AuthService):
    token, _ = svc.create_refresh_token({"sub": "u@example.com"})
    assert svc.decode_refresh_token(token) == "u@example.com"


def test_email_token_roundtrip(svc: AuthService):
    token, _ = svc.create_email_token({"sub": "u@example.com"})
    assert svc.decode_email_token(token) == "u@example.com"


def test_password_reset_token_roundtrip(svc: AuthService):
    token, _ = svc.create_password_reset_token({"sub": "u@example.com", "uid": 42})
    email, uid = svc.decode_password_reset_token(token)
    assert email == "u@example.com"
    assert uid == 42


def test_decode_access_token_wrong_scope(svc: AuthService):
    token, _ = svc.create_refresh_token({"sub": "x@example.com"})
    with pytest.raises(HTTPException) as exc:
        svc.decode_access_token(token)
    assert exc.value.status_code == 401


def test_decode_email_token_invalid_signature():
    bad = jwt.encode({"sub": "a@b.com", "scope": "email_verification"}, "wrong-key", algorithm=settings.ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        AuthService().decode_email_token(bad)
    assert exc.value.status_code == 422
