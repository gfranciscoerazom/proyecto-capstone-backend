"""
This module defines the API endpoints for user management,
including authentication, registration, and user information retrieval.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm

from api.db.database import (SessionDependency, User, UserCreate, UserPublic, authenticate_user,
                             get_current_active_user)
from api.models.Scopes import Scopes
from api.models.Tags import Tags
from api.models.Token import Token
from api.security.security import create_access_token, get_password_hash

router = APIRouter(
    prefix="/users",
    tags=[Tags.users],
)

# region Endpoints


@router.post(
    "/token",

    summary="Get an access token",
    response_description="Successful Response with the access token",
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Endpoint to obtain an access token.

    This endpoint allows users to obtain an access token by providing their
    username and password. The token can then be used to authenticate subsequent
    requests.

    \f

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the
            username and password.

    Returns:
        Token: An object containing the access token and token type.

    Raises:
        HTTPException: If the username or password is incorrect, an HTTP 401
            Unauthorized error is raised.
    """
    if not (
        user := authenticate_user(
            email=form_data.username,
            password=form_data.password
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    allowed_scopes: set[Scopes] = user.role.get_allowed_scopes()

    if not all(scope in allowed_scopes for scope in form_data.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={
                "WWW-Authenticate": f'Bearer scope="{", ".join(scope.value for scope in allowed_scopes)}"'
            },
        )

    access_token: str = create_access_token(
        data={
            "sub": user.email,
            "scopes": form_data.scopes,
        }
    )

    return Token(access_token=access_token)


@router.get(
    "/info",
    response_model=UserPublic,

    summary="Get current user",
    response_description="Successful Response with the current user",
)
async def read_users_me(
    current_user: Annotated[
        User,
        Security(
            get_current_active_user,
            scopes=[Scopes.USER]
        )
    ],
) -> User:
    """
    Retrieve the current authenticated user.

    This endpoint returns the details of the currently authenticated user.

    \f

    Args:
        current_user (User): The current active user, obtained from the dependency injection.

    Returns:
        UserPublic: The current authenticated user.
    """
    return current_user


@router.post(
    "/add",
    response_model=UserPublic,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER],
        )
    ],
    summary="Add a new user of type organizer or staff",
    response_description="Successful Response with the new user",
)
async def add_user(
    user: Annotated[
        UserCreate,

        Form(
            title="User data",
            description="The data of the user to be added",
        )
    ],
    session: SessionDependency,
) -> User:
    """
    Add a new user of type organizer or staff.

    This endpoint allows an authenticated user with the appropriate permissions
    to add a new user to the system.

    Args:
        user (UserCreate): The user details to create a new user.
        current_user (User): The current active user, obtained from the dependency injection.

    Returns:
        UserPublic: The newly created user.
    """
    hashed_password: bytes = get_password_hash(user.password)
    extra_data: dict[str, bytes] = {
        "hashed_password": hashed_password,
    }
    db_user: User = User.model_validate(user, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# endregion
