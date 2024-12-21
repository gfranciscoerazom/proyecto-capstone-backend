"""
This module contains pydantic models and functions for user management.
"""

from pathlib import Path
from typing import Annotated, Any, Literal
import uuid

import jwt
from faker import Faker
from fastapi import Depends, HTTPException, Request, UploadFile, status
from fastapi.openapi.models import Example
from fastapi.security import SecurityScopes
from pydantic import EmailStr, HttpUrl, ValidationError
from sqlmodel import Field, Session, SQLModel, select  # type: ignore

from api.db.engine import engine
from api.models.Role import Role
from api.models.Token import TokenData
from api.security.security import oauth2_scheme, verify_password
from api.settings.config import settings
from deepface import DeepFace  # type: ignore

# region vars
f = Faker()
# endregion


# region classes
class UserBase(SQLModel):
    """
    Base class for the User model.

    Contains the common fields for the User model. Used as a base class for the rest of the User models.
    """
    email: EmailStr = Field(
        index=True,
        unique=True,

        title="Email address of the user",
        description="The email address of the user. Used for authentication and identification.",
    )


class User(UserBase, table=True):
    """
    User model.

    Represents a user in the database. Used for save and retrieve user data from the database.
    """
    id: int | None = Field(
        default=None,
        primary_key=True,

        title="User ID",
        description="The unique identifier of the user.",
    )
    hashed_password: bytes = Field(
        title="Hashed Password",
        description="The hashed password of the user. Used for authentication.",
    )
    disabled: bool = Field(
        default=False,

        title="User status",
        description="The status of the user. If True, the user is disabled."
    )
    role: Role = Field(
        default=Role.ASSISTANT,

        title="User role",
        description="The role of the user. Used for authorization.",
    )
    image_url: str = Field(
        unique=True,
        index=True,

        title="Image Path",
        description="The path to the user's face image.",
    )


class UserPublic(UserBase):
    """
    Public User model.

    Represents a user in the API. Used for returning user data to the client.
    """
    id: int = Field(
        title="User ID",
        description="The unique identifier of the user.",
    )
    disabled: bool = Field(
        title="User status",
        description="The status of the user. If True, the user is disabled."
    )
    role: Role = Field(
        title="User role",
        description="The role of the user. Used for authorization.",
    )
    image_url: HttpUrl = Field(
        title="Image Path",
        description="The path to the user's face image.",
    )


class UserCreate(UserBase):
    """
    User Create model.

    Represents a user to be created in the API. Used for receiving user data from the client.
    """
    password: str = Field(
        title="Password",
        description="The password of the user. Used for authentication.",
    )
    image: UploadFile = Field(
        title="Profile Image",
        description="The profile image of the user.",
    )


class UserUpdate(SQLModel):
    """
    User Update model.

    Represents a user to be updated in the API. Used for receiving user data from the client.
    """
    email: EmailStr | None = Field(
        default=None,

        title="Email address of the user",
        description="The email address of the user. Used for authentication and identification.",
    )
    password: str | None = Field(
        default=None,

        title="Password",
        description="The password of the user. Used for authentication.",
    )
    disabled: bool | None = Field(
        default=None,

        title="User status",
        description="The status of the user. If True, the user is disabled."
    )
    role: Role | None = Field(
        default=None,

        title="User role",
        description="The role of the user. Used for authorization.",
    )
    image: UploadFile | None = Field(
        default=None,

        title="Profile Image",
        description="The profile image of the user.",
    )
# endregion


# region openapi_examples
openapi_examples_UserCreate: dict[str, Example] = {
    "Random Example 1": {
        "summary": "Random Example 1",
        "description": "A example generated with random data",
        "value": {
            "email": f.email(),
            "password": f.password(length=30),
        },
    },
    "Example 1": {
        "summary": "Example 1",
        "description": "A example of a valid user to be created",
        "value": {
            "email": "user@example.com",
            "password": "StRing12!@",
        },
    },
    "Example 2": {
        "summary": "Example 2",
        "description": "Another example of a valid user to be created",
        "value": {
            "email": "person.name@universidad.edu.ec",
            "password": "Secure4-Password6!",
        },
    },
    "Invalid Example 1": {
        "summary": "Invalid Example 1",
        "description": "An example of an invalid user to be created",
        "value": {
            "email": "invalid-email.com",
            "password": "string",
        },
    },
    "Invalid Example 2": {
        "summary": "Invalid Example 2",
        "description": "Another example of an invalid user to be created",
        "value": {
            "email": "user@example.com",
            "password": "string",
        },
    },
}
# endregion

# region functions


def get_user(
        email: EmailStr | None = None,
        user_id: int | None = None
) -> None | User:
    """
    Retrieve a user from the database by email or user ID.
    Args:
        email (EmailStr | None): The email of the user to retrieve. Defaults to None.
        user_id (int | None): The ID of the user to retrieve. Defaults to None.
    Returns:
        (User | None): The user object if found, otherwise None.
    """
    if not email and not user_id:
        return None

    with Session(engine) as session:
        if email:
            return session.exec(select(User).where(User.email == email)).first()
        if user_id:
            return session.get(User, user_id)

    return None


def authenticate_user(email: EmailStr, password: str) -> User | Literal[False]:
    """
    Authenticate a user by email and password.
    Args:
        email (EmailStr): The email of the user to authenticate.
        password (str): The password of the user to authenticate.
    Returns:
        (User | None): The user object if authenticated, otherwise None.
    """
    if not (user := get_user(email=email)):
        return False

    return user if verify_password(password, user.hashed_password) else False


def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """
    Retrieve the current user from the database using the token.

    Args:
        token (str): The token used to authenticate the user.

    Returns:
        user (User): The user object if found, otherwise raises an HTTPException

    Raises:
        credentials_exception (HTTPException): An exception raised if the credentials are invalid.
    """
    authenticate_value: str = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload: dict[str, Any] = jwt.decode(  # type: ignore
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if not (username := payload.get("sub")):
            raise credentials_exception

        token_scopes: list[str] = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except (jwt.InvalidTokenError, ValidationError):
        raise credentials_exception

    if not (user := get_user(email=token_data.username)):
        raise credentials_exception

    if not all(scope in token_data.scopes for scope in security_scopes.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": authenticate_value},
        )

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Retrieve the current active user from the database.

    Args:
        current_user (User): The current user object.

    Returns:
        current_user (User): The current user object if the user is active.

    Raises:
        HTTPException: An exception raised if the user is inactive.
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def is_single_person(image_path: Path) -> bool:
    """
    Check if the image at the given path contains exactly one person.

    Args:
        image_path (Path): The path to the image file.

    Returns:
        bool: True if the image contains exactly one person, False otherwise.
    """
    try:
        face_objs = DeepFace.extract_faces(  # type: ignore
            img_path=str(image_path),
            detector_backend="yunet",
            align=True,
        )
    except ValueError as e:
        if "Face could not be detected" in str(e):
            return False
        raise e

    return len(face_objs) == 1


async def save_user_image(user: UserCreate, request: Request) -> HttpUrl:
    """
    Save the user's image to the server.

    Args:
        user (UserCreate): The user object containing the image file.
        request (Request): The request object to get the URL details.

    Returns:
        HttpUrl: The URL where the image is saved.
    """
    new_uuid: uuid.UUID = uuid.uuid4()
    image_path: Path = Path(
        f"./data/imgs/{new_uuid}.png"
    )
    image_path.parent.mkdir(parents=True, exist_ok=True)

    with image_path.open("wb") as image_file:
        image_file.write(await user.image.read())

    if not is_single_person(image_path):
        if image_path.exists():
            image_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The image must contain exactly one person",
        )

    domain: None | str = request.url.hostname
    schema: str = request.url.scheme
    port: int | None = request.url.port
    image_url: HttpUrl = HttpUrl(
        url=f"{schema}://{domain}:{port}/data/imgs/{new_uuid}.png"
    )
    return image_url
# endregion
