"""Unit tests for password hashing helpers."""

from src.security.passwords import get_password_hash, verify_password


def test_hash_and_verify_roundtrip():
    plain = "Secret123"
    hashed = get_password_hash(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False
