from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from fastapi import Response
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set before starting the backend")
# Absolute maximum session lifetime is strictly 24 hours (1440 minutes), no sliding expiration
MAX_SESSION_MINUTES = 1440
_env_exp = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
ACCESS_TOKEN_EXPIRE_MINUTES = (
    min(int(_env_exp), MAX_SESSION_MINUTES) if _env_exp else MAX_SESSION_MINUTES
)
AUTH_COOKIE_NAME = "access_token"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def is_cookie_secure() -> bool:
    env_secure = os.getenv("COOKIE_SECURE")
    if env_secure is not None:
        return env_secure.strip().lower() in ("true", "1", "yes")
    return os.getenv("ENVIRONMENT") == "production" or bool(os.getenv("RENDER"))


def get_cookie_samesite() -> str:
    samesite = os.getenv("COOKIE_SAMESITE", "lax").strip().lower()
    if samesite not in {"lax", "strict", "none"}:
        raise RuntimeError("COOKIE_SAMESITE must be one of: lax, strict, none")
    return samesite


def set_auth_cookie(response: Response, token: str) -> None:
    """
    Sets a browser-session HttpOnly cookie with an absolute 24-hour token.
    Max-Age and Expires are deliberately omitted so the cookie is discarded
    when the browser session terminates.
    """
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_cookie_secure(),
        samesite=get_cookie_samesite(),
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """
    Clears the authentication cookie from the browser profile.
    """
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=is_cookie_secure(),
        samesite=get_cookie_samesite(),
    )


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": expire,
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt
