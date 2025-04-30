"""
This module defines the API endpoints for user management,
including authentication, registration, and user information retrieval.
"""

from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, Form, HTTPException, Security, status

from app.db.database import (Event, EventPublicWithEventDate,
                             SessionDependency, User, UserCreate, UserPublic,
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
    status_code=status.HTTP_201_CREATED,
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
    Adds a new user of type staff into the database.

    \f

    :param user: Information about the user to be added.
    :type UserCreate:
    :param session: Database session dependency to connect to the database.
    :type session: SessionDependency
    :return: The information of the user that was added to the database.
    :rtype: User
    """
    hashed_password: bytes = get_password_hash(user.password)
    extra_data: dict[str, bytes | Role] = {
        "hashed_password": hashed_password,
        "role": Role.STAFF,
    }
    db_user: User = User.model_validate(user, update=extra_data)
    session.add(db_user)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from e
    session.refresh(db_user)
    return db_user


@router.post(
    "add-staff-to-event",
    response_model=EventPublicWithEventDate,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER],
        )
    ],

    summary="Add a new user of type staff to an event",
    response_description="Successful Response with the new user",
)
async def add_staff_to_event(
    staff_id: Annotated[
        int,
        Form(
            title="Staff ID",
            description="The ID of the staff to be added to the event",
        )
    ],
    event_id: Annotated[
        int,
        Form(
            title="Event ID",
            description="The ID of the event to which the staff is to be added",
        )
    ],
    session: SessionDependency
) -> Event:
    """
    Add a new user of type staff to an event.

    This endpoint allows an authenticated user with the appropriate permissions
    to add a new user to the system.

    Args:
        staff_id (int): The ID of the staff to be added to the event.
        event_id (int): The ID of the event to which the staff is to be added.

    Returns:
        UserPublic: The newly created user.
    """
    if not (staff := session.get(User, staff_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found",
        )

    if staff.role != Role.STAFF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a staff",
        )

    if not (event := session.get(Event, event_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    event.staff.append(staff)
    try:
        session.add(event)
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Staff already added to the event",
        ) from e
    session.commit()
    session.refresh(event)
    return event

# endregion
