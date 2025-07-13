import datetime
import pathlib as pl
from typing import Annotated, Any
from uuid import UUID

import sqlalchemy
from fastapi import (APIRouter, Body, Depends, Form, HTTPException, Path, Query,
                     Security, UploadFile, status)
from fastapi.responses import FileResponse
from pydantic import PositiveInt
import sqlalchemy.exc
from sqlmodel import select

from app.db.database import (Attendance, Event, EventCreate, EventDate,
                             EventDateCreate, EventPublicWithEventDate,
                             EventPublicWithNoDeletedEventDate, EventUpdate, Registration,
                             SessionDependency, User, get_current_active_user)
from app.helpers.files import safe_path_join
from app.helpers.validations import are_unique_dates, save_image
from app.models.Scopes import Scopes
from app.models.Tags import Tags
from app.models.TypeCapacity import TypeCapacity

router = APIRouter(
    prefix="/events",
    tags=[Tags.events],
)


@router.get(
    "/upcoming",
    response_model=list[EventPublicWithNoDeletedEventDate],

    summary="Get upcoming events",
    response_description="A list of upcoming events with their dates, this event are ordered by date, from the closest to the farthest",
)
async def get_upcoming_events(
    session: SessionDependency,
    quantity: Annotated[
        int | None,
        Query(
            title="Quantity",
            description="The number of upcoming events to retrieve. If not provided, all upcoming events will be returned.",
            ge=0,
        )
    ] = None,
) -> list[Event]:
    """
    Endpoint to get a list of upcoming events.

    This endpoint allows users to retrieve a list of upcoming events, ordered by it first date from the closest to the farthest.

    \f

    :param session: The database session dependency to interact with the database.
    :type session: SessionDependency

    :param quantity: The number of upcoming events to retrieve.
    :type quantity: int | None
    """
    events = session.exec(
        select(Event)
        .join(EventDate)
        .where(
            EventDate.day_date >= datetime.datetime.now(), EventDate.deleted == False
        )
        .distinct()
    ).all()

    events = sorted(events, key=lambda event: sorted(event.event_dates)[0])

    if quantity:
        events = events[:quantity]

    return events
# region Endpoints


@router.post(
    "/add",
    response_model=EventPublicWithEventDate,
    status_code=status.HTTP_201_CREATED,

    summary="Add an event",
    response_description="The added event",
)
async def add_event(
    event: Annotated[
        EventCreate,
        Form(
            title="Event information",
            description="The information of the event to add to the database.",
            media_type="multipart/form-data",
        )
    ],
    session: SessionDependency,
    current_user: Annotated[
        User,
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER],
        )
    ],
) -> Event:
    """
    Add an event to the database.

    This endpoint allows users to add a new event to the database by providing the necessary information.

    \f

    Args:
    - event (EventPublic): The information of the event to add to the database.
    - session (SessionDependency): The database session dependency.

    Returns:
    - Event: The added event.
    """
    event_image_uuid: UUID = await save_image(image=event.image, folder="events_imgs")

    if event.capacity_type == TypeCapacity.SITE_CAPACITY:
        event.capacity -= int(event.capacity * 0.1)

    extra_data_event: dict[str, Any] = {
        "image_uuid": event_image_uuid,
        "organizer_id": current_user.id,
    }

    new_event: Event = Event.model_validate(event, update=extra_data_event)

    session.add(new_event)

    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        image_path: pl.Path = pl.Path(
            f"./data/events_imgs/{event_image_uuid}.png"
        )
        if image_path.exists():
            image_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e

    session.refresh(new_event)
    return new_event


@router.patch(
    "/{event_id}",
    response_model=EventPublicWithEventDate,
    summary="Update an event by ID",
    response_description="Successful Response with the updated event",
)
async def update_event(
    event_id: int,
    event: EventUpdate,
    session: SessionDependency
):
    """
    Update an event by ID.

    This endpoint allows users to update an existing event by providing the event ID and the updated event information.

    \f

    Args:
    - event_id (int): The ID of the event to update.
    - event (EventUpdate): The updated event information.
    - session (SessionDependency): The database session dependency.

    Returns:
    - Event: The updated event.
    """
    db_event = session.get(Event, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    event_data = event.model_dump(exclude_unset=True)
    db_event.sqlmodel_update(event_data)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


# Método para actualizar la imagen de un evento
@router.patch(
    "/{event_id}/image",
    response_model=EventPublicWithEventDate,
    summary="Update event image by ID",
    response_description="Successful Response with the updated event",
)
async def update_event_image(
    event_id: int,
    image: UploadFile,
    session: SessionDependency
):
    """
    Update the image of an event by ID.

    This endpoint allows users to update the image of an existing event by providing the event ID and the new image.

    \f

    Args:
    - event_id (int): The ID of the event to update.
    - image (UploadFile): The new image file.
    - session (SessionDependency): The database session dependency.

    Returns:
    - Event: The updated event.
    """
    db_event = session.get(Event, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Eliminar la imagen anterior si existe
    if db_event.image_uuid:
        image_path: pl.Path = pl.Path(
            f"./data/events_imgs/{db_event.image_uuid}.png"
        )
        if image_path.exists():
            image_path.unlink()

    # Guardar la nueva imagen
    new_image_uuid = await save_image(image=image, folder="events_imgs")
    db_event.image_uuid = new_image_uuid

    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


@router.get(
    "/all",
    response_model=list[EventPublicWithEventDate],
)
async def get_events(
    session: SessionDependency
):
    """
    Get all events.

    This endpoint retrieves a list of all events in the system.

    \f

    :param session: The database session dependency to connect to the database.
    :type session: SessionDependency

    :return: A list of all events.
    :rtype: list[EventPublicWithNoDeletedEventDate]
    """
    events = session.exec(
        select(Event)
    ).all()
    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No events found",
        )
    return events


@router.get(
    "/my-registered-events",

    summary="Get all events where the current user is registered",
    response_description="List of events where the current user is registered",
)
async def read_users_me(
    current_user: Annotated[
        User,
        Depends(
            get_current_active_user,
        )
    ],
    session: SessionDependency,
):
    """
    Get all events where the current user is registered.

    This endpoint retrieves a list of events that the currently authenticated user is registered for.

    :param current_user: The currently authenticated user.
    :type current_user: User

    :return: A list of events where the current user is registered.
    :rtype: list[EventPublicWithEventDate]
    """
    registrations = session.exec(
        select(Registration)
        .where(Registration.companion_id == current_user.id)
    ).all()

    if not registrations:
        return []

    event_ids = [registration.event_id for registration in registrations]
    events = session.exec(
        select(Event)
        .where(Event.id.in_(event_ids))
    ).all()

    return events


@router.get(
    "/events-to-react",
    response_model=list[EventPublicWithEventDate],
    summary="Get events to react",
    response_description="List of events to react",
)
async def get_events_to_react(
    current_user: Annotated[
        User,
        Depends(
            get_current_active_user,
        )
    ],
    session: SessionDependency,
):
    """
    Get events to react.

    This endpoint retrieves a list of events that the currently authenticated user can react to.

    :param current_user: The currently authenticated user.
    :type current_user: User

    :return: A list of events to react to.
    :rtype: list[EventPublicWithEventDate]
    """
    my_registered_events = session.exec(
        select(Registration)
        .where(Registration.companion_id == current_user.id, Registration.reaction_date == None)
    ).all()

    if not my_registered_events:
        return []

    event_ids = [
        registration.event_id for registration in my_registered_events]
    events = session.exec(
        select(Event)
        .where(Event.id.in_(event_ids))
    ).all()

    return events


@router.get(
    "/{event_id}",
    response_model=EventPublicWithEventDate,
    # dependencies=[
    #     Security(
    #         get_current_active_user,
    #         scopes=[Scopes.ORGANIZER]
    #     )
    # ],

    summary="Get an event by ID",
    response_description="Successful Response with the event",
)
async def get_event_by_id(
    event_id: Annotated[
        PositiveInt,
        Path(
            title="Event ID",
            description="The ID of the event to be retrieved.",
        )
    ],
    session: SessionDependency,
) -> Event:
    """
    Endpoint to get an event by ID.

    This endpoint allows users to retrieve an event by its ID.

    \f

    Args:
        event_id (int): The ID of the event to be retrieved.
        session (SessionDependency): The database session dependency.

    Returns:
        EventPublic: The retrieved event.

    Raises:
        HTTPException: If the event is not found.
    """
    if not (event := session.get(Event, event_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@router.get(
    "/image/{image_uuid}",
    response_class=FileResponse,

    summary="Get event image",
    response_description="Successful Response with the event image",
)
def get_event_image(
    image_uuid: Annotated[
        UUID,
        Path(
            title="Image UUID",
            description="The UUID of the event image to retrieve",
        )
    ],
) -> str:
    """
    Endpoint to obtain an event's image.

    This endpoint allows users to retrieve an event's image by providing the image's UUID.

    \f

    Args:
        image_uuid (UUID): The UUID of the event image to retrieve.

    Returns:
        FileResponse: The event's image.

    Raises:
        HTTPException: If the image is not found in the images database.
    """
    normalized_image_path: pl.Path = safe_path_join(
        pl.Path("./data/events_imgs"),
        f"{image_uuid}.png"
    )

    if not normalized_image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    return normalized_image_path.as_posix()


@router.post(
    "/{event_id}/dates/add",
    response_model=EventPublicWithEventDate,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER]
        )
    ],

    summary="Add one or more dates to an event",
    response_description="The added dates",
)
async def add_event_dates(
    event_id: Annotated[
        PositiveInt,
        Path(
            title="Event ID",
            description="The ID of the event to add dates to.",
        )
    ],
    dates: Annotated[
        list[EventDateCreate],
        Body(
            title="Event dates",
            description="The dates to be added to the event.",
        )
    ],
    session: SessionDependency,
) -> Event:
    """
    Endpoint to add one or more dates to an event.

    This endpoint allows users to add dates for a specific event by providing the event ID along with the date(s) to be added.

    \f

    Args:
        event_id (PositiveInt): The ID of the event to add dates to.
        dates (list[EventDateCreate]): The list of dates to be added.
        session (SessionDependency): The database session dependency.

    Returns:
        list[EventDatePublic]: The list of added event dates.

    Raises:
        HTTPException: If the event is not found or dates could not be added.
    """
    if not (event := session.get(Event, event_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    new_dates: list[EventDate] = [
        EventDate.model_validate(date) for date in dates]

    if not are_unique_dates(event, new_dates):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="In the provided dates, there are duplicates with the existing dates or among themselves.",
        )

    event.event_dates.extend(new_dates)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.post(
    "/{event_id}/date/add",
    response_model=EventPublicWithEventDate,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER]
        )
    ],

    summary="Add a date to an event",
    response_description="The added date",
)
async def add_event_date(
    event_id: Annotated[
        PositiveInt,
        Path(
            title="Event ID",
            description="The ID of the event to add a date to.",
        )
    ],
    date: Annotated[
        EventDateCreate,
        Form(
            title="Event date",
            description="The date to be added to the event.",
        )
    ],
    session: SessionDependency,
) -> Event:
    """
    Endpoint to add a date to an event.

    This endpoint allows users to add a date for a specific event by providing the event ID along with the date to be added.

    \f

    Args:
        event_id (PositiveInt): The ID of the event to add a date to.
        date (EventDateCreate): The date to be added.
        session (SessionDependency): The database session dependency.

    Returns:
        EventPublic: The added event date.

    Raises:
        HTTPException: If the event is not found or the date could not be added.
    """
    if not (event := session.get(Event, event_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    new_date: EventDate = EventDate.model_validate(date)

    if not are_unique_dates(event, new_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The provided date is a duplicate with an existing date.",
        )

    event.event_dates.append(new_date)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.delete(
    "/date/{event_date_id}",
    response_model=EventPublicWithEventDate,

    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER]
        )
    ],
    summary="Delete an event date",
    response_description="The deleted event date",
)
async def delete_event_date(
    event_date_id: Annotated[
        PositiveInt,
        Path(
            title="Event date ID",
            description="The ID of the event date to be deleted.",
        )
    ],
    session: SessionDependency,
) -> Event:
    """Endpoint to change to true the deleted parameter of an event date.

    :param event_date_id: The ID of the event date to be marked as deleted.
    :type event_date_id: PositiveInt
    :param session: The database session dependency.
    :type session: SessionDependency
    :return: The updated event with the deleted status.
    :rtype: Event
    """

    if not (event_date := session.get(EventDate, event_date_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event date not found",
        )

    event_date.deleted = True
    session.add(event_date)
    session.commit()
    session.refresh(event_date)

    return event_date.event


@router.post(
    "/add/attendance/{event_date_id}/{registration_id}",
    response_model=Attendance,
    # dependencies=[
    #     Security(
    #         get_current_active_user,
    #         scopes=[Scopes.STAFF]
    #     )
    # ],

    summary="Add an attendance to an event",
    response_description="The added attendance",
)
async def add_attendance(
    event_date_id: Annotated[
        PositiveInt,
        Path(
            title="Event date ID",
            description="The ID of the event date to add an attendance to.",
        )
    ],
    registration_id: Annotated[
        PositiveInt,
        Path(
            title="Registration ID",
            description="The ID of the registration to add an attendance to.",
        )
    ],
    session: SessionDependency,
) -> Attendance:
    """
    Endpoint to add an attendance to an event.

    This endpoint allows users to register attendance for a specific event date by providing the event ID, event date ID, and registration ID.

    \f

    :param event_date_id: The ID of the event date to add attendance to.
    :type event_date_id: PositiveInt
    :param registration_id: The ID of the registration to add attendance for.
    :type registration_id: PositiveInt
    :param session: The database session dependency.
    :type session: SessionDependency
    :return: The added attendance.
    :rtype: Attendance
    """
    if not (event_date := session.get(EventDate, event_date_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event date not found",
        )

    if not (registration := session.get(Registration, registration_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found",
        )

    # Verificar que la fecha del evento no esté eliminada
    if event_date.deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event date is deleted",
        )

    # Verificar que la fecha del evento pertenezca a un evento en el cual el usuario está registrado
    if event_date.event_id != registration.event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event date does not belong to the event of the registration",
        )

    new_attendance: Attendance = Attendance(
        event_date=event_date,
        registration=registration,
    )

    session.add(new_attendance)
    # session.commit()
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    session.refresh(new_attendance)

    return new_attendance


@router.post(
    "/add/attendance/{event_date_id}/{event_id}/{companion_id}",
    response_model=Attendance,
    summary="Add an attendance to an event",
    response_description="The added attendance",
)
async def add_attendance_by_companion(
    event_date_id: Annotated[
        PositiveInt,
        Path(
            title="Event date ID",
            description="The ID of the event date to add an attendance to.",
        )
    ],
    event_id: Annotated[
        PositiveInt,
        Path(
            title="Event ID",
            description="The ID of the event to add an attendance to.",
        )
    ],
    companion_id: Annotated[
        PositiveInt,
        Path(
            title="Companion ID",
            description="The ID of the companion to add an attendance to.",
        )
    ],
    session: SessionDependency,
):
    """
    Endpoint to add an attendance to an event.

    This endpoint allows users to register attendance for a specific event date by providing the event ID, event date ID, and companion ID.

    \f

    :param event_date_id: The ID of the event date to add attendance to.
    :type event_date_id: PositiveInt
    :param event_id: The ID of the event to add attendance to.
    :type event_id: PositiveInt
    :param companion_id: The ID of the companion to add attendance for.
    :type companion_id: PositiveInt
    :param session: The database session dependency.
    :type session: SessionDependency
    :return: The added attendance.
    :rtype: Attendance
    """
    if not (registration := session.exec(
        select(Registration)
        .where(
            Registration.event_id == event_id,
            Registration.companion_id == companion_id,
        )
    ).first()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found",
        )

    if not (event_date := session.get(EventDate, event_date_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event date not found",
        )

    attendance = Attendance(
        event_date=event_date,
        registration=registration,
    )

    session.add(attendance)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    session.refresh(attendance)

    return attendance


@router.delete(
    "/{event_id}",
    response_model=EventPublicWithEventDate,

    summary="Delete an event",
    response_description="The deleted event",
)
async def delete_event(
    event_id: Annotated[
        PositiveInt,
        Path(
            title="Event ID",
            description="The ID of the event to be deleted.",
        )
    ],
    session: SessionDependency,
) -> Event:
    """
    Endpoint to delete an event.

    This endpoint allows users to delete an event by its ID.

    \f

    :param event_id: The ID of the event to be deleted.
    :type event_id: PositiveInt
    :param session: The database session dependency.
    :type session: SessionDependency
    :return: The deleted event.
    :rtype: Event
    """
    if not (event := session.get(Event, event_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    session.delete(event)
    session.commit()

    return event


@router.get(
    "/{event_id}/dates",
    response_model=list[EventDate],
)
async def get_event_dates(
    event_id: Annotated[
        PositiveInt,
        Path(
            title="Event ID",
            description="The ID of the event to get dates for.",
        )
    ],
    session: SessionDependency,
) -> list[EventDate]:
    """
    Endpoint to get all dates for a specific event.

    This endpoint allows users to retrieve all dates associated with a specific event by its ID.

    \f

    :param event_id: The ID of the event to get dates for.
    :type event_id: PositiveInt
    :param session: The database session dependency.
    :type session: SessionDependency
    :return: A list of event dates.
    :rtype: list[EventDate]
    """
    if not (event := session.get(Event, event_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event.event_dates

# endregion
