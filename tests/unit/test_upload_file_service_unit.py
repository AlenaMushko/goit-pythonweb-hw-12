"""Unit tests for Cloudinary avatar helpers."""

from unittest.mock import MagicMock, patch

from src.services.upload_file_service import UploadFileService


def test_get_avatar_public_id_contains_user():
    assert "user_7" in UploadFileService.get_avatar_public_id(7)


def test_upload_avatar_returns_secure_url():
    with patch("src.services.upload_file_service.cloudinary.uploader.upload") as upload:
        upload.return_value = {"secure_url": "https://cdn.example/img.png"}

        url = UploadFileService.upload_avatar("/tmp/x.png", "folder/id")

    assert url == "https://cdn.example/img.png"
    upload.assert_called_once()
