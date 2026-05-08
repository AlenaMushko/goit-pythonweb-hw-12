VERSION = {
    "v1": "v1",
}

API_VERSION = VERSION["v1"]

PREFIX = {
    "api": f"/api/{API_VERSION}",
    "auth": "/auth",
    "users": "/users",
    "contacts": "/contacts",
}

API_PREFIX = PREFIX["api"]
AUTH_PREFIX = PREFIX["auth"]
USERS_PREFIX = PREFIX["users"]
CONTACTS_PREFIX = PREFIX["contacts"]
CONFIRMED_EMAIL_PATH = "/confirmed_email"
RESET_PASSWORD_PATH = "/reset_password"
RESET_PASSWORD_CONFIRM_PATH = "/reset_password/confirm"
CLOUDINARY_AVATARS_FOLDER = "contacts_api"
ALLOWED_AVATAR_CONTENT_TYPES = ("image/png", "image/jpeg", "image/webp")
MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024

NAME_MAX_LENGTH = 30
EMAIL_MAX_LENGTH = 50
PHONE_MAX_LENGTH = 20
ADDITIONAL_INFO_MAX_LENGTH = 150

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
PHONE_REGEX = r"^\+?[0-9]{7,20}$"
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
