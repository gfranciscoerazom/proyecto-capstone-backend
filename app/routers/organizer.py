"""
This module defines the API endpoints for user management,
including authentication, registration, and user information retrieval.
"""

from typing import Annotated

import logfire
import sqlalchemy
from fastapi import APIRouter, Form, HTTPException, Security, status

from app.db.database import (SessionDependency, User, UserCreate, UserPublic,
                             get_current_active_user)
from app.models.Role import Role
from app.models.Scopes import Scopes
from app.models.Tags import Tags
from app.security.security import get_password_hash

router = APIRouter(
    prefix="/organizer",
    tags=[Tags.organizer],
)

# region Endpoints


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
    summary="Add a new user of type organizer",
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
    current_user: Annotated[User, Security(get_current_active_user, scopes=[Scopes.ORGANIZER])],
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
    extra_data: dict[str, bytes | Role] = {
        "hashed_password": hashed_password,
        "role": Role.ORGANIZER,
    }
    db_user: User = User.model_validate(user, update=extra_data)
    session.add(db_user)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organizer with this email already exists",
        ) from e
    session.refresh(db_user)
    logfire.info(f"User {db_user.email} added by {current_user.email}")
    return db_user

# endregion
