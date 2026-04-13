from __future__ import annotations

import base64
import binascii
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from .settings import get_settings

_JWT_DECODE_OPTIONS = {
    "verify_signature": True,
    "verify_exp": True,
}

JWT_ALG = "HS256"


def hash_password(password: str) -> str:
    s = get_settings()
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, s.pbkdf2_iterations, dklen=32)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    hash_b64 = base64.urlsafe_b64encode(dk).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${s.pbkdf2_iterations}${salt_b64}${hash_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iter_s, salt_b64, hash_b64 = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_s)

        def _b64decode_nopad(x: str) -> bytes:
            pad = "=" * (-len(x) % 4)
            return base64.urlsafe_b64decode(x + pad)

        salt = _b64decode_nopad(salt_b64)
        expected = _b64decode_nopad(hash_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=len(expected))
        return secrets.compare_digest(actual, expected)
    except (ValueError, TypeError, binascii.Error, UnicodeEncodeError):
        return False


def create_access_token(*, user_id: int) -> str:
    s = get_settings()
    now = datetime.now(tz=UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=s.jwt_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=JWT_ALG)


class TokenPayload:
    def __init__(self, user_id: int):
        self.user_id = user_id


def decode_token(token: str) -> TokenPayload:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[JWT_ALG], options=_JWT_DECODE_OPTIONS)
    except JWTError as e:
        raise ValueError("Invalid token") from e

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Invalid token payload")
    try:
        user_id = int(sub)
    except (TypeError, ValueError) as e:
        raise ValueError("Invalid subject in token") from e
    return TokenPayload(user_id=user_id)
