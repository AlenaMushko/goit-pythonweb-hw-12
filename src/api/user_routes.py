from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.constants import USERS_PREFIX
from src.db.session import get_db
from src.models.user_model import UserModel
from src.models.user_role import UserRole
from src.schemas.user_schemas import UserResponse
from src.services.auth_service import get_current_user
from src.services.user_service import UserService
from src.utils.rate_limiter import limiter

router = APIRouter(prefix=USERS_PREFIX, tags=["users"])


@router.get("/me", response_model=UserResponse)
@limiter.limit("5/minute")
async def get_me(
    request: Request,
    current_user: UserModel = Depends(get_current_user),
):
    return current_user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update avatar",
        )
    user_service = UserService(db)
    return await user_service.update_avatar(file, current_user)
