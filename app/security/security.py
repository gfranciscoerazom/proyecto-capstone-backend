"""
This module provides security related functions, including password hashing,
verification, and JWT token creation.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi.security import OAuth2PasswordBearer

from app.models.Scopes import scopes
from app.settings.config import settings

# region variables
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token",
    scopes=scopes,  # type: ignore
)
# endregion


# region helpers
def verify_password(plain_password: str, hashed_password: bytes):
    """
    Verify that a plain text password matches a hashed password.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (bytes): The hashed password to compare against.

    Returns:
        bool: True if the plain password matches the hashed password, False otherwise.
    """
    password_byte_enc = plain_password.encode('utf-8')
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password)


def get_password_hash(password: str):
    """Hashes a password using bcrypt.

    Hashes a given password using the configured password context.

    :param password: The plain text password to be hashed.
    :type password: str
    :return: The hashed password.
    :rtype: bytes
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password


def create_access_token(
        data: dict[str, Any],
        expires_delta: timedelta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
) -> str:
    """
    Create a JSON Web Token (JWT) for the given data with an expiration time.

    Args:
        data (dict[str, Any]): The data to include in the token payload.
        expires_delta (timedelta, optional): The time duration after which the token will expire.

    Returns:
        str: The encoded JWT as a string.
    """
    to_encode = data.copy()
    expire: datetime = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(  # type: ignore
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# endregion
