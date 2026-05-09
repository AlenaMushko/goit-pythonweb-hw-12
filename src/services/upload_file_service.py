import logging

import cloudinary
import cloudinary.uploader
from cloudinary import CloudinaryImage
from cloudinary.utils import cloudinary_url

from src.conf.config import settings
from src.conf.constants import CLOUDINARY_AVATARS_FOLDER

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

logger = logging.getLogger(__name__)


class UploadFileService:
    """Utility service for Cloudinary avatar operations."""
    @staticmethod
    def get_avatar_public_id(user_id: int) -> str:
        """Build Cloudinary public id for a user avatar."""
        return f"{CLOUDINARY_AVATARS_FOLDER}/user_{user_id}"

    @staticmethod
    def upload_avatar(file_path: str, public_id: str) -> str:
        """Upload avatar to Cloudinary and return secure URL."""
        logger.debug("Uploading avatar to Cloudinary: file_path=%s public_id=%s", file_path, public_id)

        try:
            response = cloudinary.uploader.upload(file_path, public_id=public_id, overwrite=True)
            return response.get("secure_url")

        except Exception:
            logger.exception("Cloudinary avatar upload failed")
            raise

    @staticmethod
    def delete_avatar(public_id: str) -> None:
        """Delete avatar from Cloudinary by public id."""
        cloudinary.uploader.destroy(public_id, invalidate=True)
