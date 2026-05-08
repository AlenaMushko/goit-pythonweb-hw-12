from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors

from src.conf.config import settings
from src.conf.constants import API_PREFIX, AUTH_PREFIX, CONFIRMED_EMAIL_PATH
from src.utils.logger import Logger

logger = Logger()


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent.parent / "templates",
)


async def send_verification_email(recipient_email: str, token: str, fullname: str = "") -> None:
    base_host = settings.VERIFY_EMAIL_HOST.rstrip("/")
    verify_path = f"{API_PREFIX}{AUTH_PREFIX}{CONFIRMED_EMAIL_PATH}/{token}"
    verify_url = f"{base_host}{verify_path}"
    display_name = fullname.strip() or recipient_email

    if not settings.MAIL_SERVER or not settings.MAIL_FROM:
        logger.warning(
            f"MAIL_SERVER or MAIL_FROM are missing. Verification link for {recipient_email}: {verify_url}",
            title="EmailService",
        )
        return

    message = MessageSchema(
        subject="Confirm your email",
        recipients=[recipient_email],
        template_body={
            "verify_url": verify_url,
            "fullname": display_name,
        },
        subtype=MessageType.html,
    )

    fm = FastMail(conf)

    try:
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as exc:
        logger.error(
            f"Failed to send verification email to {recipient_email}: {exc}",
            title="EmailService",
        )
