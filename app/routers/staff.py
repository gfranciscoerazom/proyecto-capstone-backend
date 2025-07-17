"""
This module defines the API endpoints for user management,
including authentication, registration, and user information retrieval.
"""
from typing import Annotated

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from fastapi import APIRouter, Form, HTTPException, Security, status

from app.db.database import (Event, EventPublicWithEventDate,
                             SessionDependency, StaffEventLink, User, UserCreate, UserPublic, UserUpdate,
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
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from e
    session.refresh(db_user)
    return db_user


@router.post(
    "/add-staff-to-event",
    response_model=EventPublicWithEventDate,
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
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Staff already added to the event",
        ) from e
    session.commit()
    session.refresh(event)
    return event


@router.get(
    "/my-events",
    response_model=list[EventPublicWithEventDate],
    summary="Get all events where the current staff member is assigned",
    response_description="List of events where the current staff member is assigned",
)
async def get_my_events(
    current_user: Annotated[
        User,
        Security(
            get_current_active_user,
            scopes=[Scopes.STAFF],
        )
    ],
    session: SessionDependency,
):
    """
    Get all events where the current staff member is assigned.

    This endpoint retrieves a list of events that the currently authenticated
    staff member is assigned to.

    :param current_user: The currently authenticated user.
    :type current_user: User

    :param session: Database session dependency to connect to the database.
    :type session: SessionDependency

    :return: A list of events where the current staff member is assigned.
    :rtype: list[EventPublicWithEventDate]
    """
    events = list(session.exec(
        select(Event).join(StaffEventLink).where(
            StaffEventLink.staff_id == current_user.id
        )
    ).all())
    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No events found for the current staff member",
        )
    return events


@router.get(
    "/all",
    response_model=list[UserPublic],
    summary="Obtener todos los de staff",
    response_description="Lista de usuarios con rol STAFF"
)
async def list_staffss(
    session: SessionDependency
):
    """
    Recupera todos los usuarios cuyo rol sea STAFF.
    Requiere autenticación con el scope STAFF.
    """
    staffs = session.exec(
        select(User).where(User.role == Role.STAFF)
    ).all()

    return staffs


@router.patch(
    "/{staff_id}",
    response_model=UserPublic,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER],
        )
    ],
    summary="Actualizar parcialmente un miembro del staff",
    response_description="Usuario actualizado exitosamente"
)
async def update_staff(
    staff_id: int,
    user_update: UserUpdate,
    session: SessionDependency
) -> User:
    """
    Actualiza parcialmente un usuario con rol STAFF.
    
    Este endpoint permite a un organizador actualizar parcialmente
    la información de un miembro del staff.
    
    Args:
        staff_id (int): El ID del miembro del staff a actualizar.
        user_update (UserUpdate): Los datos a actualizar del usuario.
        session (SessionDependency): Sesión de la base de datos.
    
    Returns:
        UserPublic: El usuario actualizado.
    
    Raises:
        HTTPException: Si el usuario no existe o no es un miembro del staff.
    """
    # Verificar que el usuario existe
    staff = session.get(User, staff_id)
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    
    # Verificar que el usuario es staff
    if staff.role != Role.STAFF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a staff member"
        )
    
    # Actualizar solo los campos que no son None
    user_data = user_update.model_dump(exclude_unset=True)
    
    # Si se está actualizando la contraseña, hashearla
    if "password" in user_data:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    
    # Actualizar los campos del usuario
    for field, value in user_data.items():
        setattr(staff, field, value)
    
    try:
        session.add(staff)
        session.commit()
        session.refresh(staff)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists or data conflict"
        ) from e
    
    return staff


@router.delete(
    "/{staff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER],
        )
    ],
    summary="Eliminar un miembro del staff",
    response_description="Usuario eliminado exitosamente"
)
async def delete_staff(
    staff_id: int,
    session: SessionDependency
):
    """
    Elimina un usuario con rol STAFF del sistema.
    
    Este endpoint permite a un organizador eliminar completamente
    un miembro del staff del sistema.
    
    Args:
        staff_id (int): El ID del miembro del staff a eliminar.
        session (SessionDependency): Sesión de la base de datos.
    
    Raises:
        HTTPException: Si el usuario no existe o no es un miembro del staff.
    """
    # Verificar que el usuario existe
    staff = session.get(User, staff_id)
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    
    # Verificar que el usuario es staff
    if staff.role != Role.STAFF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a staff member"
        )
    
    try:
        session.delete(staff)
        session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete staff member due to existing relationships"
        ) from e

# endregion
