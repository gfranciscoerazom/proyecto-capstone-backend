"""
This module defines the API endpoints for user management,
including authentication, registration, and user information retrieval.
"""

import os
from typing import Annotated, Any

import logfire
import sqlalchemy.exc
from fastapi import APIRouter, Form, HTTPException, Query, Security, status
from sqlmodel import select

from app.db.database import (SessionDependency, User, UserCreate, UserPublic, UserUpdate,
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


@router.get(
    "/get-settings",
    summary="Get the current face recognition AI model settings",
)
async def get_face_recognition_ai_model() -> dict[str, Any]:
    """
    Retrieve the current settings for the face recognition AI model.

    Returns:
        dict[str, Any]: A dictionary containing the current model and threshold.
    """
    return {
        "model": settings.FACE_RECOGNITION_AI_MODEL,
        "threshold": settings.FACE_RECOGNITION_AI_THRESHOLD,
    }


@router.get(
    "/all",
    response_model=list[UserPublic],
    summary="Obtener todos los organizadores",
    response_description="Lista de usuarios con rol ORGANIZER"
)
async def list_organizers(
    session: SessionDependency
):
    """
    Recupera todos los usuarios cuyo rol sea ORGANIZER.
    Requiere autenticación con el scope ORGANIZER.
    """
    organizers = session.exec(
        select(User).where(User.role == Role.ORGANIZER)
    ).all()

    return organizers


@router.patch(
    "/{organizer_id}",
    response_model=UserPublic,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER],
        )
    ],
    summary="Actualizar parcialmente un organizador",
    response_description="Organizador actualizado exitosamente"
)
async def update_organizer(
    organizer_id: int,
    organizer_update: UserUpdate,
    session: SessionDependency,
    current_user: Annotated[User, Security(get_current_active_user, scopes=[Scopes.ORGANIZER])],
) -> User:
    """
    Actualiza parcialmente un organizador existente.

    Este endpoint permite a un usuario autenticado con permisos apropiados
    actualizar parcialmente los datos de un organizador específico.

    Args:
        organizer_id (int): ID del organizador a actualizar.
        organizer_update (UserUpdate): Datos parciales para actualizar el organizador.
        session (SessionDependency): Sesión de base de datos.
        current_user (User): Usuario actual autenticado.

    Returns:
        UserPublic: El organizador actualizado.

    Raises:
        HTTPException: Si el organizador no existe o no tiene rol ORGANIZER.
    """
    # Buscar el organizador existente
    organizer = session.get(User, organizer_id)
    if not organizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organizador no encontrado",
        )
    
    # Verificar que el usuario sea un organizador
    if organizer.role != Role.ORGANIZER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario especificado no es un organizador",
        )

    # Actualizar solo los campos proporcionados
    organizer_data = organizer_update.model_dump(exclude_unset=True)
    
    # Si se está actualizando la contraseña, hashearla
    if "password" in organizer_data:
        organizer_data["hashed_password"] = get_password_hash(organizer_data.pop("password"))
    
    # Aplicar las actualizaciones
    for field, value in organizer_data.items():
        setattr(organizer, field, value)

    try:
        session.add(organizer)
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email ya existe para otro usuario",
        ) from e
    
    session.refresh(organizer)
    logfire.info(f"Organizador {organizer.email} actualizado por {current_user.email}")
    return organizer


@router.delete(
    "/{organizer_id}",
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER],
        )
    ],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un organizador",
    response_description="Organizador eliminado exitosamente"
)
async def delete_organizer(
    organizer_id: int,
    session: SessionDependency,
    current_user: Annotated[User, Security(get_current_active_user, scopes=[Scopes.ORGANIZER])],
) -> None:
    """
    Elimina un organizador del sistema.

    Este endpoint permite a un usuario autenticado con permisos apropiados
    eliminar un organizador específico del sistema.

    Args:
        organizer_id (int): ID del organizador a eliminar.
        session (SessionDependency): Sesión de base de datos.
        current_user (User): Usuario actual autenticado.

    Raises:
        HTTPException: Si el organizador no existe, no tiene rol ORGANIZER,
                      o si intenta eliminarse a sí mismo.
    """
    # Buscar el organizador existente
    organizer = session.get(User, organizer_id)
    if not organizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organizador no encontrado",
        )
    
    # Verificar que el usuario sea un organizador
    if organizer.role != Role.ORGANIZER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario especificado no es un organizador",
        )
    
    # Prevenir que un organizador se elimine a sí mismo
    if organizer.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminarte a ti mismo",
        )

    session.delete(organizer)
    session.commit()
    logfire.info(f"Organizador {organizer.email} eliminado por {current_user.email}")


# endregion
