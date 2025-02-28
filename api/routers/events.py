from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Security, status

from api.db.database import Event, EventCreate, EventPublic, SessionDependency, get_current_active_user
from api.db.validations import save_image
from api.models.Scopes import Scopes
from api.models.Tags import Tags

router = APIRouter(
    prefix="/events",
    tags=[Tags.events],
)

# region Endpoints


@router.post(
    "/add",
    response_model=EventPublic,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER]
        )
    ],

    summary="Add an event",
    response_description="The added event",
)
async def add_event(
    event: Annotated[
        EventCreate,
        Form(
            title="Event information",
            description="The information of the event to add to the database.",
        )
    ],
    session: SessionDependency,
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
    if bool(event.max_capacity) ^ bool(event.venue_capacity):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either max_capacity or venue_capacity should be provided, not both.",
        )

    event_image_uuid: UUID = await save_image(image=event.image, folder="events_imgs")
    new_event: Event = Event.model_validate(event)
    new_event.image_uuid = event_image_uuid
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return new_event


@router.get(
    "/",
    response_model=EventPublic,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.ORGANIZER]
        )
    ],

    summary="Get an event by ID",
    response_description="Successful Response with the event",
)
async def get_event_by_id(
    event_id: Annotated[
        int,
        Path(
            ge=1,

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
# endregion
