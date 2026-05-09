"""Unit tests for email helpers when SMTP is not configured."""

from unittest.mock import MagicMock, patch

import pytest

from src.services import email_service


@pytest.mark.asyncio
async def test_send_verification_email_logs_when_mail_not_configured(monkeypatch):
    monkeypatch.setattr(
        email_service.settings,
        "VERIFY_EMAIL_HOST",
        "http://localhost:9999",
    )
    monkeypatch.setattr(email_service.settings, "MAIL_SERVER", None)
    monkeypatch.setattr(email_service.settings, "MAIL_FROM", None)

    with patch.object(email_service.logger, "warning") as warn:
        await email_service.send_verification_email("u@example.com", "tok", "Name")

    warn.assert_called_once()


@pytest.mark.asyncio
async def test_send_password_reset_email_logs_when_mail_not_configured(monkeypatch):
    monkeypatch.setattr(email_service.settings, "VERIFY_EMAIL_HOST", "http://localhost:9999")
    monkeypatch.setattr(email_service.settings, "MAIL_SERVER", None)
    monkeypatch.setattr(email_service.settings, "MAIL_FROM", None)

    with patch.object(email_service.logger, "warning") as warn:
        await email_service.send_password_reset_email("u@example.com", "tok")

    warn.assert_called_once()
