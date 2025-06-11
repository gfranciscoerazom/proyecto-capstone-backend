import pathlib as pl
from typing import Annotated
from uuid import UUID

import sqlalchemy
from deepface import DeepFace  # type: ignore
from fastapi import (APIRouter, BackgroundTasks, File, Form, HTTPException,
                     Path, Query, Security, UploadFile, status)
from fastapi.responses import FileResponse
import sqlalchemy.exc
from sqlmodel import select

from app.db.database import (Assistant, AssistantCreate, Event, Registration,
                             RegistrationPublic, SessionDependency, User,
                             UserAssistantCreate, UserAssistantPublic,
                             UserCreate, get_current_active_user)
from app.helpers.dateAndTime import get_quito_time
from app.helpers.files import safe_path_join
from app.helpers.mail import send_event_registration_email, send_new_assistant_email, send_event_rating_email, send_registration_canceled_email
from app.helpers.validations import save_user_image
from app.models.Reaction import Reaction
from app.models.Role import Role
from app.models.Scopes import Scopes
from app.models.Tags import Tags
from app.models.TypeCompanion import TypeCompanion
from app.security.security import get_password_hash
from app.settings.config import settings

router = APIRouter(
    prefix="/assistant",
    tags=[Tags.assistants],
)


@router.post(
    "/add",
    response_model=UserAssistantPublic,
    status_code=status.HTTP_201_CREATED,

    summary="Add a new user",
    response_description="Successful Response with the new user",
)
async def add_assistant(
    user_assistant: Annotated[
        UserAssistantCreate,

        Form(
            title="Assistant data",
            description="The data of the assistant to be added",
            media_type="multipart/form-data",
        )
    ],
    session: SessionDependency,
    background_tasks: BackgroundTasks,
) -> User:
    """
    Endpoint to add a new assistant.

    This endpoint allows people to create a new account by providing the necessary
    information.

    \f

    Args:
        user_assistant (UserAssistantCreate): The assistant information to create a new account.
        session (SessionDependency): The database session dependency.

    Returns:
        UserAssistant: The newly created assistant.

    Raises:
        HTTPException: If the password validation fails.
    """
    user: UserCreate = user_assistant.get_user()
    assistant: AssistantCreate = user_assistant.get_assistant()

    async def delete_temp_image(temp_image_path: pl.Path):
        if temp_image_path.exists():
            temp_image_path.unlink()

    temp_image_uuid: UUID = await save_user_image(assistant.image, folder="temp_imgs")
    temp_image_path: pl.Path = pl.Path(
        "./data/temp_imgs"
    ) / f"{temp_image_uuid}.png"

    # try:
    images_df = DeepFace.find(  # type: ignore
        img_path=str(temp_image_path),
        db_path=str(pl.Path("./data/people_imgs")),
        model_name=settings.FACE_RECOGNITION_AI_MODEL,
        threshold=settings.FACE_RECOGNITION_AI_THRESHOLD,
        detector_backend="yunet",
    )
    # except UnidentifiedImageError:

    #     print("No hay una persona con esa img uwu")
    #     images_df = []

    if len(images_df[0]) > 1:
        await delete_temp_image(temp_image_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is more than one assistant with the same image",
        )

    hashed_password: bytes = get_password_hash(user.password)

    # image_uuid: UUID = await save_user_image(assistant.image)
    # En vez de guardar la imagen en el disco mueve la imagen que está en temp_imgs a people_imgs
    image_uuid: UUID = temp_image_uuid
    image_path: pl.Path = pl.Path(
        f"./data/temp_imgs/{image_uuid}.png"
    )
    image_path.rename(
        pl.Path(f"./data/people_imgs/{image_uuid}.png")
    )

    extra_data_user: dict[str, bytes | Role] = {
        "hashed_password": hashed_password,
        "role": Role.ASSISTANT,
    }

    extra_data_assistant: dict[str, UUID] = {
        "image_uuid": image_uuid,
    }

    db_user: User = User.model_validate(user, update=extra_data_user)
    db_assistant: Assistant = Assistant.model_validate(
        assistant,
        update=extra_data_assistant
    )

    db_user.assistant = db_assistant

    session.add(db_user)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        image_path: pl.Path = pl.Path(
            f"./data/people_imgs/{image_uuid}.png"
        )
        if image_path.exists():
            image_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e
    session.refresh(db_user)

    background_tasks.add_task(
        send_new_assistant_email,
        db_user
    )

    return db_user


@router.post(
    "/get-by-image",
    response_model=list[UserAssistantPublic],
    # dependencies=[
    #     Security(
    #         get_current_active_user,
    #         scopes=[Scopes.STAFF],
    #     )
    # ],
    summary="Get users by image provided",
    response_description="Successful Response with a list of users found that are similar to the person in the image",
)
async def get_assistants_by_image(
    image: Annotated[
        UploadFile,
        File(
            title="Image of a registered user",
            description="A image of a registered user to use it to find the user",
        )
    ],
    session: SessionDependency,
) -> list[User]:
    """
    Endpoint to obtain assistants by image.

    This endpoint allows staff to find registered assistants by providing an image.
    The image is compared against the database to find similar assistants.

    \f

    Args:
        image (UploadFile): The image of a registered assistant.
        session (SessionDependency): The database session dependency.

    Returns:
        list[UserAssistant]: A list of assistants found that are similar to the person in the image.

    Raises:
        HTTPException: If no assistants are found in the images database or the main database.
    """
    async def delete_temp_image(temp_image_path: pl.Path):
        if temp_image_path.exists():
            temp_image_path.unlink()

    temp_image_uuid: UUID = await save_user_image(image, folder="temp_imgs")
    temp_image_path: pl.Path = pl.Path(
        "./data/temp_imgs"
    ) / f"{temp_image_uuid}.png"

    images_df = DeepFace.find(  # type: ignore
        img_path=str(temp_image_path),
        db_path=str(pl.Path("./data/people_imgs")),
        model_name=settings.FACE_RECOGNITION_AI_MODEL,
        threshold=settings.FACE_RECOGNITION_AI_THRESHOLD,
        detector_backend="yunet",
    )

    if len(images_df[0]) < 1:
        await delete_temp_image(temp_image_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found in images database",
        )

    assistants: list[Assistant] = [
        session.exec(
            select(Assistant).
            where(
                Assistant.image_uuid == UUID(pl.Path(img).stem)  # type: ignore
            )
        ).first()
        for img in images_df[0]['identity']  # type: ignore
    ]

    if not all(assistants):
        await delete_temp_image(temp_image_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found in database",
        )

    await delete_temp_image(temp_image_path)

    return list(map(lambda assistant: assistant.user, assistants))


@router.get(
    "/get-by-id-number/{id_number}",
    response_model=UserAssistantPublic,
    # dependencies=[
    #     Security(
    #         get_current_active_user,
    #         scopes=[Scopes.STAFF],
    #     )
    # ],
    summary="Get user by ID number",
    response_description="Successful Response with the user found",
)
def get_user_by_id_number(
    id_number: Annotated[
        str,
        Path(
            min_length=8,
            max_length=10,
            title="ID number",
            description="The ID number of the user to search for",
        )
    ],
    session: SessionDependency,
) -> User:
    """
    Endpoint to obtain a user by ID number.

    This endpoint allows staff to find a registered user by providing their ID number.

    \f

    Args:
        id_number (str): The ID number of the user to search for.
        session (SessionDependency): The database session dependency.

    Returns:
        UserAssistant: The user found with the provided ID number.

    Raises:
        HTTPException: If the user is not found in the database.
    """

    if not (
        assistant := session.exec(
            select(Assistant).
            where(
                Assistant.id_number == id_number
            )
        ).first()
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found",
        )

    return assistant.user


@router.get(
    "/image/{image_uuid}",
    response_class=FileResponse,

    summary="Get user image",
    response_description="Successful Response with the user image",
)
def get_user_image(
    image_uuid: Annotated[
        UUID,
        Path(
            title="Image UUID",
            description="The UUID of the image to retrieve",
        )
    ],
) -> str:
    """
    Endpoint to obtain a user's image.

    This endpoint allows users to retrieve their image by providing the image's UUID.

    \f

    Args:
        image_uuid (UUID): The UUID of the image to retrieve.

    Returns:
        FileResponse: The user's image.

    Raises:
        HTTPException: If the image is not found in the images database.
    """
    try:
        normalized_image_path: pl.Path = safe_path_join(
            pl.Path("./data/people_imgs"),
            f"{image_uuid}.png"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image path",
        )

    if not normalized_image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    return normalized_image_path.as_posix()


@router.post(
    "/register-to-event/{event_id}",
    response_model=RegistrationPublic,
    summary="Register to an event",
    response_description="Successful Response with the registration",
)
def register_to_event(
    event_id: Annotated[
        int,
        Path(
            title="Event ID",
            description="The ID of the event to register to",
        )
    ],
    session: SessionDependency,
    current_user: Annotated[
        User,
        Security(
            get_current_active_user,
            scopes=[Scopes.ASSISTANT]
        )
    ],
    background_tasks: BackgroundTasks,
) -> Registration:
    """
    Endpoint to register to an event.

    This endpoint allows users to register to an event by providing the event's ID.

    \f

    Args:
        event_id (int): The ID of the event to register to.
        session (SessionDependency): The database session dependency.
        current_user (User): The current active user, obtained from the dependency injection.

    Returns:
        Registration: The registration to the event.

    Raises:
        HTTPException: If the event is not found in the database.
    """
    if not (user := session.get(User, current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not (event := session.get(Event, event_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if not (assistant := session.get(Assistant, current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found",
        )

    registration: Registration = Registration(
        event=event,
        assistant=user,
        companion=assistant,
        companion_type=TypeCompanion.ZERO_GRADE
    )

    session.add(registration)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e
    session.refresh(registration)

    background_tasks.add_task(
        send_event_registration_email,
        current_user,
        event,
        event.event_dates
    )

    return registration


@router.post(
    "/register-companion-to-event/{event_id}",
    response_model=RegistrationPublic,

    summary="Register a companion to an event",
    response_description="Successful Response with the registration",
)
def register_companion_to_event(
    event_id: Annotated[
        int,
        Path(
            title="Event ID",
            description="The ID of the event to register a companion to",
        )
    ],
    companion_id: Annotated[
        int,
        Form(
            title="Companion ID",
            description="The ID of the companion to register to the event",
        )
    ],
    companion_type: Annotated[
        TypeCompanion,
        Form(
            title="Companion type",
            description="The type of the companion to register to the event",
        )
    ],
    session: SessionDependency,
    current_user: Annotated[
        User,
        Security(
            get_current_active_user,
            scopes=[Scopes.ASSISTANT]
        )
    ],
) -> Registration:
    """
    Endpoint to register a companion to an event.

    This endpoint allows users to register a companion to an event by providing the event's ID
    and the companion's ID.

    \f

    Args:
        event_id (int): The ID of the event to register a companion to.
        companion_id (int): The ID of the companion to register to the event.
        session: SessionDependency: The database session dependency.
        current_user (User): The current active user, obtained from the dependency injection.

    Returns:
        Registration: The registration of the companion to the event.

    Raises:
        HTTPException: If the event or the companion is not found in the database.
    """
    if not (user := session.get(User, current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not (event := session.get(Event, event_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if not (companion := session.get(Assistant, companion_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companion not found",
        )

    # Verificar que el usuario esté registrado en el evento al que quiere registrar a su acompañante
    user_events = session.exec(
        select(Event).
        join(Registration).
        where(
            Registration.assistant_id == user.id
        )
    ).all()

    if event not in user_events:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not registered for this event",
        )

    registration: Registration = Registration(
        event=event,
        assistant=user,
        companion=companion,
        companion_type=companion_type,
    )

    session.add(registration)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e
    session.refresh(registration)

    return registration


@router.get(
    "/react/{user_id}/{event_id}",
    response_model=RegistrationPublic,
    summary="React to an event",
    response_description="Successful Response",
)
def react_to_event(
    user_id: Annotated[
        int,
        Path(
            title="User ID",
            description="The ID of the user to react to the event",
        )
    ],
    event_id: Annotated[
        int,
        Path(
            title="Event ID",
            description="The ID of the event to react to",
        )
    ],
    reaction: Annotated[
        Reaction,
        Query(
            title="Reaction",
            description="The reaction to the event",
        )
    ],
    session: SessionDependency,
    background_tasks: BackgroundTasks,  # <-- Add this parameter
) -> Registration:
    """
    Endpoint to react to an event.

    This endpoint allows users to react to an event by providing the user ID,
    event ID, and the reaction.

    \f

    :param user_id: The ID of the user reacting to the event
    :type user_id: int
    :param event_id: The ID of the event to react to
    :type event_id: int
    :param reaction: The reaction to the event
    :type reaction: Reaction
    :param session: The database session
    :type session: SessionDependency
    """

    if not (user := session.get(User, user_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not (event := session.get(Event, event_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if not (registration := session.exec(
        select(Registration).
        where(
            Registration.companion_id == user.id,
            Registration.event_id == event.id
        )
    ).first()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found",
        )

    registration.reaction = reaction
    registration.reaction_date = get_quito_time()

    session.add(registration)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e
    session.refresh(registration)

    # Send rating email after reacting
    background_tasks.add_task(
        send_event_rating_email,
        user
    )

    return registration


@router.get(
    "/get-registered-events",
    response_model=list[RegistrationPublic],

    summary="Get registered events",
    response_description="Successful Response with the list of registered events",
)
def get_registered_events(
    current_user: Annotated[
        User,
        Security(
            get_current_active_user,
            scopes=[Scopes.ASSISTANT]
        )
    ],
    background_tasks: BackgroundTasks,
    session: SessionDependency
):
    """
    Endpoint to get registered events for a user.

    This endpoint allows users to retrieve a list of events they are registered for.

    :param user_id: The ID of the user to get registered events for
    :type user_id: int
    :param session: The database session
    :type session: SessionDependency
    """
    print(f"Current user ID: {current_user.id}")
    registrations = session.exec(
        select(Registration).
        where(Registration.assistant_id == current_user.id,
              Registration.companion_id == current_user.id)
    ).all()

    # try:
    #     background_tasks.add_task(
    #         send_event_registration_email,
    #         current_user
    #     ) # type: ignore
    # except Exception as e:
    #     print(f"Error sending email: {e}")
    
    return registrations

# response = requests.post(
#     f"{settings.API_URL}/assistant/unregister-from-event/{event_id}",
#     headers={"Authorization": f"Bearer {access_token}"}
# )


@router.delete(
    "/unregister-from-event/{event_id}",
    response_model=RegistrationPublic,

    summary="Unregister from an event",
    response_description="Successful Response with the unregistration",
)
def unregister_from_event(
    event_id: Annotated[
        int,
        Path(
            title="Event ID",
            description="The ID of the event to unregister from",
        )
    ],
    session: SessionDependency,
    current_user: Annotated[
        User,
        Security(
            get_current_active_user,
            scopes=[Scopes.ASSISTANT]
        )
    ],
    background_tasks: BackgroundTasks,
):
    """Endpoint to unregister from an event.
    This endpoint allows users to unregister from an event by providing the event's ID.

    :param event_id: The ID of the event to unregister from
    :type event_id: int
    :param session: The database session
    :type session: SessionDependency
    :param current_user: The user who is unregistering from the event
    :type current_user: User
    """
    registration = session.exec(
        select(Registration).
        where(
            Registration.event_id == event_id,
            Registration.companion_id == current_user.id
        )
    ).first()

    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found",
        )

    session.delete(registration)
    try:
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e

    event = session.get(Event, event_id)
    
    background_tasks.add_task(
        send_registration_canceled_email,
        current_user,
        event
    )

    return registration