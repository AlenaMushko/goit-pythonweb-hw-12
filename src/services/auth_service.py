from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.db.session import get_db
from src.models.token_model import TokenType
from src.models.user_model import UserModel
from src.repositories.token_repository import TokenRepository
from src.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer()


class AuthService:
    def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> tuple[str, datetime]:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire, "scope": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt, expire

    def create_refresh_token(self, data: dict, expires_delta: timedelta | None = None) -> tuple[str, datetime]:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        to_encode.update({"exp": expire, "scope": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt, expire

    def create_email_token(self, data: dict) -> tuple[str, datetime]:
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=7)
        to_encode.update(
            {
                "iat": now,
                "exp": expire,
                "scope": "email_verification",
            }
        )
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM), expire

    def create_password_reset_token(self, data: dict) -> tuple[str, datetime]:
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        to_encode.update(
            {
                "iat": now,
                "exp": expire,
                "scope": "password_reset",
            }
        )
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM), expire

    def decode_email_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("scope") != "email_verification":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid token scope for email verification",
                )
            email = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid token payload",
                )
            return email
        except JWTError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid or expired email verification token",
            ) from error

    def decode_access_token(self, token: str) -> str:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("scope") != "access":
                raise credentials_exception
            email: str | None = payload.get("sub")
            if email is None:
                raise credentials_exception
            return email
        except JWTError as error:
            raise credentials_exception from error

    def decode_refresh_token(self, token: str) -> str:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("scope") != "refresh":
                raise credentials_exception
            email: str | None = payload.get("sub")
            if email is None:
                raise credentials_exception
            return email
        except JWTError as error:
            raise credentials_exception from error

    def decode_password_reset_token(self, token: str) -> tuple[str, int]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("scope") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid token scope for password reset",
                )
            email = payload.get("sub")
            user_id = payload.get("uid")
            if email is None or user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid token payload",
                )
            return str(email), int(user_id)
        except JWTError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid or expired password reset token",
            ) from error


auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("scope") != "access":
            raise credentials_exception
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as error:
        raise credentials_exception from error

    token_repository = TokenRepository(db)
    active_access_token = await token_repository.get_active_token(token, TokenType.ACCESS)
    if active_access_token is None:
        raise credentials_exception

    user_repository = UserRepository(db)
    user = await user_repository.get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user
