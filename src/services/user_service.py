import os
import tempfile
import logging

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.conf.constants import ALLOWED_AVATAR_CONTENT_TYPES, MAX_AVATAR_SIZE_BYTES
from src.models.user_model import UserModel
from src.repositories.user_repository import UserRepository
from src.services.upload_file_service import UploadFileService

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def update_avatar(self, file: UploadFile, current_user: UserModel):
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Avatar filename is required",
            )

        if file.content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Use image/png, image/jpeg, or image/webp.",
            )

        if not all(
            [
                settings.CLOUDINARY_CLOUD_NAME,
                settings.CLOUDINARY_API_KEY,
                settings.CLOUDINARY_API_SECRET,
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloudinary is not configured on the server",
            )

        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Avatar file is empty",
            )

        if len(content) > MAX_AVATAR_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Avatar file is too large. Max allowed size is {MAX_AVATAR_SIZE_BYTES} bytes.",
            )

        suffix = os.path.splitext(file.filename or "")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            public_id = UploadFileService.get_avatar_public_id(current_user.id)
            if current_user.avatar:
                UploadFileService.delete_avatar(public_id)
            avatar_url = UploadFileService.upload_avatar(temp_path, public_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Avatar upload failed for user_id=%s", current_user.id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to upload avatar to cloud storage",
            ) from exc
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return await self.repository.update_avatar(current_user, avatar_url)
