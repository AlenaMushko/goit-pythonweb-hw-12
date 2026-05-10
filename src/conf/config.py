from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    # Used by docker-compose naming only; DATABASE_URL drives the real connection.
    POSTGRES_CONTAINER_NAME: str = "n/a"
    POSTGRES_USER: str = "n/a"
    POSTGRES_PASSWORD: str = "n/a"
    POSTGRES_DB: str = "n/a"

    POSTGRES_PORT: str = "5432"

    DATABASE_URL: str
    REDIS_URL: str
    REDIS_USER_CACHE_TTL_SECONDS: int = 3600

    APP_CONTAINER_NAME: str = "n/a"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: str = "8003"

    FRONTEND_ORIGIN: str = "*"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_PORT: int = 587
    MAIL_SERVER: str | None = None
    MAIL_FROM_NAME: str = "Contacts API"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VERIFY_EMAIL_HOST: str = "http://localhost:8003"

    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None
    CLOUDINARY_URL: str | None = None
    TOKEN_CLEANUP_INTERVAL_SECONDS: int = 604800

    model_config = ConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: object) -> object:
        """Fly Postgres attach uses postgres://; SQLAlchemy async needs asyncpg scheme."""
        if not isinstance(v, str):
            return v
        if v.startswith("postgres://"):
            return "postgresql+asyncpg://" + v.removeprefix("postgres://")
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return "postgresql+asyncpg://" + v.removeprefix("postgresql://")
        return v


settings = Settings()
origins = [
    origin.strip()
    for origin in settings.FRONTEND_ORIGIN.split(",")
    if origin.strip()
]