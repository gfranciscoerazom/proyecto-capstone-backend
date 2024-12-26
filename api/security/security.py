"""
This module provides security related functions, including password hashing,
verification, and JWT token creation.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from api.models.Scopes import scopes
from api.settings.config import settings

# region variables
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/token",
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
    """
    Hashes a given password using the configured password context.

    Args:
        password (str): The plain text password to be hashed.

    Returns:
        bytes: The hashed password.
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


def validate_password(password: str) -> None:
    """
    Validate the password according to the defined rules.

    Args:
        password (str): The password to validate.

    Raises:
        HTTPException: If the password does not meet the required criteria.
    """
    if (
        len(password) < 9 or
        len(re.findall(r"[a-z]", password)) < 3 or
        len(re.findall(r"[A-Z]", password)) < 2 or
        len(re.findall(r"\d", password)) < 2 or
        len(re.findall(r"[¡!@#$%^¿?&*()\-_+./\\]", password)) < 2
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 3 lowercase, 2 uppercase, 2 digits, 2 special character and be at least 9 characters long.",
        )
# endregion
