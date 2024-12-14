"""
This module defines the API endpoints for user management,
including authentication, registration, and user information retrieval.
"""

import re
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm

from api.db.setup import SessionDependency
from api.models.Scopes import Scopes
from api.models.Tags import Tags
from api.models.Token import Token
from api.models.User import (User, UserCreate, UserPublic, authenticate_user,
                             get_current_active_user,
                             openapi_examples_UserCreate)
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

    access_token: str = create_access_token(
        data={
            "sub": user.email,
            "scopes": [user.role]
        }
    )

    return Token(access_token=access_token)


@router.get(
    "/me/",
    response_model=UserPublic,

    summary="Get current user",
    response_description="Successful Response with the current user",
)
async def read_users_me(
    current_user: Annotated[
        User,
        Security(
            get_current_active_user,
            scopes=[Scopes.ASSISTANT, Scopes.ADMIN]
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
    "/sign-up",
    response_model=UserPublic,

    summary="Sign up a new user",
    response_description="Successful Response with the new user",
)
async def sign_up(
    user: Annotated[
        UserCreate,
        Body(
            title="User to create",
            description="The user to be created",
            openapi_examples=openapi_examples_UserCreate,
        )
    ],
    session: SessionDependency
) -> User:
    if not re.match(
        "^(?=(.*[a-z]){3,})(?=(.*[A-Z]){2,})(?=(.*[0-9]){2,})(?=(.*[!@#$%^&*()\\-__+.]){2,}).{9,}$",
        user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 3 lowercase, 2 uppercase, 2 digits, 2 special character and be at least 8 characters long.",
        )

    hashed_password: bytes = get_password_hash(user.password)
    extra_data: dict[str, bytes] = {"hashed_password": hashed_password}
    db_user: User = User.model_validate(user, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
# endregion
