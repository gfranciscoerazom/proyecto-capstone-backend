"""
This module defines the API endpoints for user management,
including authentication, registration, and user information retrieval.
"""

import os
from typing import Annotated, Any

import logfire
import sqlalchemy
from fastapi import APIRouter, Form, HTTPException, Query, Security, status

from app.db.database import (SessionDependency, User, UserCreate, UserPublic,
                             get_current_active_user)
from app.models.FaceRecognitionAiModel import FaceRecognitionAiModel
from app.models.Role import Role
from app.models.Scopes import Scopes
from app.models.Tags import Tags
from app.security.security import get_password_hash
from app.settings.config import settings, update_settings

router = APIRouter(
    prefix="/organizer",
    tags=[Tags.organizer],
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
    status_code=status.HTTP_201_CREATED,
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


@router.patch(
    "/change-settings",
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER],
        )
    ],
    summary="Change the face recognition AI model",
)
async def change_face_recognition_ai_model(
    model_name: Annotated[
        FaceRecognitionAiModel | None,
        Query(
            title="Face Recognition AI Model",
            description="The name of the face recognition AI model to be set",
        )
    ] = None,
    threshold: Annotated[
        float | None,
        Query(
            title="Face Recognition AI Threshold",
            description="The threshold for face recognition AI model to be set (0 to reset)",
        )
    ] = None,
) -> dict[str, Any]:
    if model_name:
        os.environ["FACE_RECOGNITION_AI_MODEL"] = model_name.value

    if threshold:
        os.environ["FACE_RECOGNITION_AI_THRESHOLD"] = str(threshold)

    if threshold == 0:
        del os.environ["FACE_RECOGNITION_AI_THRESHOLD"]

    update_settings()

    return {
        "model": settings.FACE_RECOGNITION_AI_MODEL,
        "threshold": settings.FACE_RECOGNITION_AI_THRESHOLD,
    }


# endregion
