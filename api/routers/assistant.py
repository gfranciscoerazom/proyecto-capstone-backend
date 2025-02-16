import pathlib as pl
from typing import Annotated
from uuid import UUID

from deepface import DeepFace  # type: ignore
from fastapi import (APIRouter, File, Form, HTTPException, Path, Security,
                     UploadFile, status)
from sqlmodel import select

from api.db.database import (Assistant, AssistantCreate, SessionDependency,
                             User, UserAssistantCreate, UserAssistantPublic,
                             UserCreate, get_current_active_user,
                             save_user_image)
from api.models.Scopes import Scopes
from api.models.Tags import Tags
from api.security.security import get_password_hash, validate_password

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
async def add_user(
    user_assistant: Annotated[
        UserAssistantCreate,

        Form(
            title="Assistant data",
            description="The data of the assistant to be added",
            media_type="multipart/form-data",
        )
    ],
    session: SessionDependency,
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

    validate_password(user.password)

    hashed_password: bytes = get_password_hash(user.password)

    image_uuid: UUID = await save_user_image(assistant.image)

    extra_data_user: dict[str, bytes] = {
        "hashed_password": hashed_password,
    }

    extra_data_assistant: dict[str, UUID] = {
        "image_uuid": image_uuid,
    }

    db_user: User = User.model_validate(user, update=extra_data_user)
    db_assistant: Assistant = Assistant.model_validate(
        assistant, update=extra_data_assistant)

    db_user.assistant = db_assistant

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@router.post(
    "/get-by-image",
    response_model=list[UserAssistantPublic],
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.STAFF],
        )
    ],
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
    ) / f"{temp_image_uuid.hex}.png"

    images_df = DeepFace.find(  # type: ignore
        img_path=str(temp_image_path),
        db_path=str(pl.Path("./data/imgs")),
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
                Assistant.image_uuid == UUID(Path(img).stem)  # type: ignore
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
    "/get-by-id-number/",
    response_model=UserAssistantPublic,
    dependencies=[
        Security(
            get_current_active_user,
            scopes=[Scopes.STAFF],
        )
    ],
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
