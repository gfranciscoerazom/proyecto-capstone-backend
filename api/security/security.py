from datetime import datetime, timedelta, timezone
from typing import Any, Final

import bcrypt
import jwt
from fastapi.security import OAuth2PasswordBearer

from api.models.Scopes import scopes

# region variables
SECRET_KEY: Final[str] = "50a2ebe353eebd0eada632ded3770850a00e8d968f2f455adaf5569780f1b51e"
ALGORITHM: Final[str] = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 30

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/token",
    # TODO: Determine if omitting the scopes parameter is a good idea.
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
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
):
    """
    Create a JSON Web Token (JWT) for the given data with an expiration time.

    Args:
        data (dict[str, Any]): The data to include in the token payload.
        expires_delta (timedelta, optional): The time duration after which the token will expire. 

    Returns:
        str: The encoded JWT as a string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(  # type: ignore
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return encoded_jwt
# endregion
