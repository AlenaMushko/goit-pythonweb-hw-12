import re

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.constants import (
    AUTH_PREFIX,
    CONFIRMED_EMAIL_PATH,
    PASSWORD_REGEX,
    RESET_PASSWORD_CONFIRM_PATH,
    RESET_PASSWORD_PATH,
)
from src.db.session import get_db
from src.models.token_model import TokenType
from src.repositories.auth_repository import AuthRepository
from src.repositories.token_repository import TokenRepository
from src.repositories.user_repository import UserRepository
from src.schemas.user_schemas import (
    PasswordResetConfirm,
    RefreshTokenRequest,
    RequestEmail,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from src.security.passwords import get_password_hash, verify_password
from src.services.auth_service import auth_service
from src.services.email_service import send_password_reset_email, send_verification_email
from src.services.password_reset_page_service import render_password_reset_page

router = APIRouter(prefix=AUTH_PREFIX, tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user and send verification email.

    Args:
        body: User registration payload.
        background_tasks: FastAPI background task manager.
        db: Active asynchronous database session.

    Returns:
        Created user object.

    Raises:
        HTTPException: If account with email already exists.
    """
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
    """
    Authenticate user and issue access and refresh tokens.

    Args:
        body: User login credentials.
        db: Active asynchronous database session.

    Returns:
        Token response payload with access and refresh tokens.

    Raises:
        HTTPException: If credentials are invalid or email is unverified.
    """
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
    await token_repository.delete_user_tokens_by_type(user_id, TokenType.REFRESH)
    access_token, access_token_expires_at = auth_service.create_access_token(data={"sub": user_email})
    refresh_token, refresh_token_expires_at = auth_service.create_refresh_token(data={"sub": user_email})
    await token_repository.create_token(
        access_token,
        user_id,
        TokenType.ACCESS,
        access_token_expires_at,
    )
    await token_repository.create_token(
        refresh_token,
        user_id,
        TokenType.REFRESH,
        refresh_token_expires_at,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate refresh token and return a fresh token pair.

    Args:
        body: Refresh token request payload.
        db: Active asynchronous database session.

    Returns:
        New access and refresh tokens.

    Raises:
        HTTPException: If refresh token is invalid or user is missing.
    """
    user_email = auth_service.decode_refresh_token(body.refresh_token)
    token_repository = TokenRepository(db)
    active_refresh_token = await token_repository.get_active_token(body.refresh_token, TokenType.REFRESH)
    if active_refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid, expired, or revoked",
        )

    user_repository = UserRepository(db)
    user = await user_repository.get_user_by_email(user_email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for refresh token",
        )

    user_id = user.id
    new_access_token, access_expires_at = auth_service.create_access_token(data={"sub": user_email})
    new_refresh_token, refresh_expires_at = auth_service.create_refresh_token(data={"sub": user_email})

    await token_repository.delete_token(active_refresh_token)
    await token_repository.delete_user_tokens_by_type(user_id, TokenType.ACCESS)
    await token_repository.create_token(
        new_access_token,
        user_id,
        TokenType.ACCESS,
        access_expires_at,
    )
    await token_repository.create_token(
        new_refresh_token,
        user_id,
        TokenType.REFRESH,
        refresh_expires_at,
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get(f"{CONFIRMED_EMAIL_PATH}/{{token}}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirm user email by verification token.

    Args:
        token: Email verification token.
        db: Active asynchronous database session.

    Returns:
        Message payload about verification status.

    Raises:
        HTTPException: If token or user is invalid.
    """
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
    """
    Resend verification email for unverified account.

    Args:
        body: Payload with user email.
        background_tasks: FastAPI background task manager.
        db: Active asynchronous database session.

    Returns:
        Generic success message payload.
    """
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


@router.post(RESET_PASSWORD_PATH, status_code=status.HTTP_200_OK)
async def request_password_reset(
    body: RequestEmail, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """
    Issue password reset token and send reset email.

    Args:
        body: Payload with user email.
        background_tasks: FastAPI background task manager.
        db: Active asynchronous database session.

    Returns:
        Generic success message payload.
    """
    user_repository = UserRepository(db)
    user = await user_repository.get_user_by_email(body.email)

    if user:
        user_id = user.id
        user_email = user.email
        user_fullname = f"{user.first_name} {user.last_name}".strip()
        token_repository = TokenRepository(db)
        await token_repository.delete_user_tokens_by_type(user_id, TokenType.PASSWORD_RESET)
        reset_token, reset_token_expires_at = auth_service.create_password_reset_token(
            {"sub": user_email, "uid": user_id}
        )
        await token_repository.create_token(
            reset_token,
            user_id,
            TokenType.PASSWORD_RESET,
            reset_token_expires_at,
        )

        background_tasks.add_task(send_password_reset_email, user_email, reset_token, user_fullname)

    return {
        "message": "If an account with this email exists, password reset instructions have been sent"
    }


@router.get(f"{RESET_PASSWORD_PATH}/{{token}}", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def validate_password_reset_token(token: str, db: AsyncSession = Depends(get_db)):
    """
    Validate reset token and return HTML reset page.

    Args:
        token: Password reset token.
        db: Active asynchronous database session.

    Returns:
        HTML page with password reset form.

    Raises:
        HTTPException: If reset token is invalid or expired.
    """
    token_repository = TokenRepository(db)
    active_token = await token_repository.get_active_token(token, TokenType.PASSWORD_RESET)
    if active_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token is invalid, expired, or already used",
        )

    _, user_id = auth_service.decode_password_reset_token(token)
    return render_password_reset_page(
        token=token,
        user_id=user_id,
        message="Token is valid. Enter your new password below.",
    )


@router.post(f"{RESET_PASSWORD_PATH}/{{token}}", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def submit_password_reset_form(
    token: str,
    password: str = Form(...),
    confirm_password: str = Form(...),
    user_id: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle password reset form submission from HTML page.

    Args:
        token: Password reset token.
        password: New password value.
        confirm_password: Confirmation password value.
        user_id: Optional user identifier from form.
        db: Active asynchronous database session.

    Returns:
        HTML page with operation result message.
    """
    if password != confirm_password:
        return HTMLResponse(
            render_password_reset_page(
                token=token,
                user_id=user_id,
                message="Password and confirm password do not match.",
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    token_repository = TokenRepository(db)
    active_token = await token_repository.get_active_token(token, TokenType.PASSWORD_RESET)
    if active_token is None:
        return HTMLResponse(
            render_password_reset_page(
                token=token,
                message="Password reset token is invalid, expired, or already used.",
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    token_email, token_user_id = auth_service.decode_password_reset_token(token)
    if user_id is not None and user_id != token_user_id:
        return HTMLResponse(
            render_password_reset_page(
                token=token,
                user_id=user_id,
                message="Token does not belong to provided user.",
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user_repository = UserRepository(db)
    user = await user_repository.get_user_by_id(token_user_id)
    if user is None or user.email != token_email:
        return HTMLResponse(
            render_password_reset_page(
                token=token,
                message="User for this token was not found.",
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    cleaned_password = password.strip()
    if not re.match(PASSWORD_REGEX, cleaned_password):
        return HTMLResponse(
            render_password_reset_page(
                token=token,
                user_id=token_user_id,
                message="Password must contain uppercase, lowercase, and number.",
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    hashed_password = get_password_hash(cleaned_password)
    user_id = user.id
    await user_repository.update_password(user, hashed_password)
    await token_repository.delete_token(active_token)
    await token_repository.delete_user_tokens_by_type(user_id, TokenType.ACCESS)
    await token_repository.delete_user_tokens_by_type(user_id, TokenType.REFRESH)

    return HTMLResponse(
        render_password_reset_page(
            token=token,
            message="Password has been reset successfully. You can close this page and log in.",
        )
    )


@router.post(RESET_PASSWORD_CONFIRM_PATH, status_code=status.HTTP_200_OK)
async def confirm_password_reset(body: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """
    Reset user password using JSON payload and reset token.

    Args:
        body: Password reset confirmation payload.
        db: Active asynchronous database session.

    Returns:
        Success message payload.

    Raises:
        HTTPException: If token or payload validation fails.
    """
    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirm password do not match",
        )

    token_repository = TokenRepository(db)
    active_token = await token_repository.get_active_token(body.token, TokenType.PASSWORD_RESET)
    if active_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token is invalid, expired, or already used",
        )

    token_email, token_user_id = auth_service.decode_password_reset_token(body.token)
    if token_user_id != body.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not belong to provided user",
        )

    user_repository = UserRepository(db)
    user = await user_repository.get_user_by_id(body.user_id)
    if user is None or user.email != token_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User for this token was not found",
        )

    hashed_password = get_password_hash(body.password)
    user_id = user.id
    await user_repository.update_password(user, hashed_password)
    await token_repository.delete_token(active_token)
    await token_repository.delete_user_tokens_by_type(user_id, TokenType.ACCESS)
    await token_repository.delete_user_tokens_by_type(user_id, TokenType.REFRESH)

    return {"message": "Password has been reset successfully"}
