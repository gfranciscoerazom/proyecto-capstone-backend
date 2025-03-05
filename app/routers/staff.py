"""
This module defines the API endpoints for user management,
including authentication, registration, and user information retrieval.
"""

from typing import Annotated

from fastapi import APIRouter, Form, Security

from app.db.database import (SessionDependency, User, UserCreate, UserPublic,
                             get_current_active_user)
from app.models.Role import Role
from app.models.Scopes import Scopes
from app.models.Tags import Tags
from app.security.security import get_password_hash

router = APIRouter(
    prefix="/staff",
    tags=[Tags.staff],
)

# region Endpoints


@router.post(
    "/add",
    response_model=UserPublic,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER],
        )
    ],
    summary="Add a new user of type staff",
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
    extra_data: dict[str, bytes | Role] = {
        "hashed_password": hashed_password,
        "role": Role.STAFF,
    }
    db_user: User = User.model_validate(user, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# endregion
