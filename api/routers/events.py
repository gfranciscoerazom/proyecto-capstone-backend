
from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Security, status

from api.db.setup import SessionDependency
from api.models.Event import Event, EventCreate, EventPublic
from api.models.Scopes import Scopes
from api.models.Tags import Tags
from api.models.User import get_current_active_user


router = APIRouter(
    prefix="/events",
    tags=[Tags.events],
)

# region Variables
HTTPException404EventNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Event not found",
)
# endregion

# region Endpoints


@router.post(
    "/add",
    response_model=EventPublic,
    dependencies=[Security(get_current_active_user, scopes=[Scopes.ADMIN])],

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
    new_event: Event = Event.model_validate(event)
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return new_event
# endregion