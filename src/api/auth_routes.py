from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.constants import AUTH_PREFIX, CONFIRMED_EMAIL_PATH
from src.db.session import get_db
from src.models.token_model import TokenType
from src.repositories.auth_repository import AuthRepository
from src.repositories.token_repository import TokenRepository
from src.repositories.user_repository import UserRepository
from src.schemas.user_schemas import RequestEmail, Token, UserCreate, UserLogin, UserResponse
from src.security.passwords import get_password_hash, verify_password
from src.services.auth_service import auth_service
from src.services.email_service import send_verification_email

router = APIRouter(prefix=AUTH_PREFIX, tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user_repository = UserRepository(db)
    existing_user = await user_repository.get_user_by_email(body.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists",
        )

    hashed_password = get_password_hash(body.password)
    user = await user_repository.create_user(body, hashed_password, None)
    user_id = user.id
    user_email = user.email
    user_fullname = f"{user.first_name} {user.last_name}".strip()

    token_repository = TokenRepository(db)
    email_token, email_token_expires_at = auth_service.create_email_token({"sub": user_email})
    await token_repository.create_token(
        email_token,
        user_id,
        TokenType.EMAIL_VERIFICATION,
        email_token_expires_at,
    )
    background_tasks.add_task(send_verification_email, user_email, email_token, user_fullname)
    created_user = await user_repository.get_user_by_email(user_email)
    return created_user


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    body: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    user_repository = UserRepository(db)
    user = await user_repository.get_user_by_email(body.email)

    if user is None or not verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email is not verified",
        )

    user_id = user.id
    user_email = user.email
    token_repository = TokenRepository(db)
    await token_repository.delete_user_tokens_by_type(user_id, TokenType.ACCESS)
    access_token, access_token_expires_at = auth_service.create_access_token(data={"sub": user_email})
    await token_repository.create_token(
        access_token,
        user_id,
        TokenType.ACCESS,
        access_token_expires_at,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(f"{CONFIRMED_EMAIL_PATH}/{{token}}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    token_repository = TokenRepository(db)
    active_email_token = await token_repository.get_active_token(token, TokenType.EMAIL_VERIFICATION)
    if active_email_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is invalid, expired, or already used",
        )

    email = auth_service.decode_email_token(token)
    user_repository = UserRepository(db)
    user = await user_repository.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification error",
        )
    if user.is_verified:
        await token_repository.delete_token(active_email_token)
        return {"message": "Your email is already verified"}

    auth_repository = AuthRepository(db)
    await auth_repository.confirm_email(user)
    await token_repository.delete_token(active_email_token)
    return {"message": "Email verified"}


@router.post("/request_email_verification")
async def request_email_verification(
    body: RequestEmail, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    user_repository = UserRepository(db)
    user = await user_repository.get_user_by_email(body.email)
    if user and not user.is_verified:
        user_id = user.id
        user_email = user.email
        user_fullname = f"{user.first_name} {user.last_name}".strip()
        token_repository = TokenRepository(db)
        await token_repository.delete_user_tokens_by_type(user_id, TokenType.EMAIL_VERIFICATION)
        email_token, email_token_expires_at = auth_service.create_email_token({"sub": user_email})
        await token_repository.create_token(
            email_token,
            user_id,
            TokenType.EMAIL_VERIFICATION,
            email_token_expires_at,
        )
        background_tasks.add_task(send_verification_email, user_email, email_token, user_fullname)
    return {
        "message": "If an account with this email exists and is not yet verified, a verification link has been sent"
    }
