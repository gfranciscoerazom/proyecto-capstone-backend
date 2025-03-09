import pathlib as pl
from typing import Annotated
from uuid import UUID

import sqlalchemy
from deepface import DeepFace  # type: ignore
from fastapi import (APIRouter, BackgroundTasks, File, Form, HTTPException,
                     Path, Security, UploadFile, status)
from fastapi.responses import FileResponse
from sqlmodel import select

from app.db.database import (Assistant, AssistantCreate, SessionDependency,
                             User, UserAssistantCreate, UserAssistantPublic,
                             UserCreate, get_current_active_user)
from app.helpers.mail import send_new_assistant_email
from app.helpers.validations import save_user_image
from app.models.Role import Role
from app.models.Scopes import Scopes
from app.models.Tags import Tags
from app.security.security import get_password_hash

router = APIRouter(
    prefix="/assistant",
    tags=[Tags.assistants],
)


@router.get(
    "/info",
    response_model=UserAssistantPublic,

    summary="Get current user",
    response_description="Successful Response with the current user",
)
async def read_users_me(
    current_user: Annotated[
        User,
        Security(
            get_current_active_user,
            scopes=[Scopes.USER]
        )
    ],
) -> User:
    """
    Retrieve the current authenticated user.

    This endpoint returns the details of the currently authenticated user.

    \f

    Args:
        current_user (User): The current active user, obtained from the dependency injection.

    Returns:
        UserAssistant: The current authenticated user.
    """
    return current_user


@router.post(
    "/add",
    response_model=UserAssistantPublic,

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

    hashed_password: bytes = get_password_hash(user.password)

    image_uuid: UUID = await save_user_image(assistant.image)

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
        model_name="Facenet512",
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
    image_path: pl.Path = pl.Path(
        f"./data/people_imgs/{image_uuid}.png"
    )

    if not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    return image_path.as_posix()
