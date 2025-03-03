import pathlib as pl
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Path, Security, status
import sqlalchemy
from fastapi.responses import FileResponse

from api.db.database import (Event, EventCreate, EventPublic,
                             SessionDependency, get_current_active_user)
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
    # dependencies=[
    #     Security(
    #         get_current_active_user,
    #         scopes=[Scopes.ORGANIZER]
    #     )
    # ],

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
    if not bool(event.max_capacity) ^ bool(event.venue_capacity):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either max_capacity or venue_capacity should be provided, not both.",
        )

    event_image_uuid: UUID = await save_image(image=event.image, folder="events_imgs")

    extra_data_event: dict[str, UUID] = {
        "image_uuid": event_image_uuid,
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    session.refresh(new_event)
    return new_event


@router.get(
    "/{event_id}",
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
    image_path: pl.Path = pl.Path(
        f"./data/events_imgs/{image_uuid}.png"
    )

    if not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    return image_path.as_posix()
# endregion
