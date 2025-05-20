import datetime
import pathlib as pl
from typing import Annotated, Any
from uuid import UUID

import sqlalchemy
from fastapi import (APIRouter, Body, Form, HTTPException, Path, Query,
                     Security, status)
from fastapi.responses import FileResponse
from pydantic import PositiveInt
from sqlmodel import select

from app.db.database import (Attendance, Event, EventCreate, EventDate,
                             EventDateCreate, EventPublicWithEventDate,
                             EventPublicWithNoDeletedEventDate, Registration,
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


# endregion
