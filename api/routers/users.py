"""
This module defines the API endpoints for user management,
including authentication, registration, and user information retrieval.
"""

from pathlib import Path
from typing import Annotated
from uuid import UUID

from deepface import DeepFace  # type: ignore
from fastapi import (APIRouter, Depends, File, Form, HTTPException, Security,
                     UploadFile, status)
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from api.db.setup import SessionDependency
from api.models.Role import Role
from api.models.Scopes import Scopes
from api.models.Tags import Tags
from api.models.Token import Token
from api.models.User import (User, UserCreate, UserPublic, authenticate_user,
                             get_current_active_user,
                             openapi_examples_UserCreate, save_user_image)
from api.security.security import (create_access_token, get_password_hash,
                                   validate_password)

router = APIRouter(
    prefix="/users",
    tags=[Tags.users],
)

# region Variables
HTTPException404UserNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found",
)
# endregion


# region Endpoints
@router.post(
    "/token",

    summary="Get an access token",
    response_description="Successful Response with the access token",
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Endpoint to obtain an access token.

    This endpoint allows users to obtain an access token by providing their
    username and password. The token can then be used to authenticate subsequent
    requests.

    \f

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the
            username and password.

    Returns:
        Token: An object containing the access token and token type.

    Raises:
        HTTPException: If the username or password is incorrect, an HTTP 401
            Unauthorized error is raised.
    """
    if not (
        user := authenticate_user(
            email=form_data.username,
            password=form_data.password
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    allowed_scopes: set[Scopes] = user.role.get_allowed_scopes()

    if not all(scope in allowed_scopes for scope in form_data.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={
                "WWW-Authenticate": f'Bearer scope="{", ".join(scope.value for scope in allowed_scopes)}"'
            },
        )

    access_token: str = create_access_token(
        data={
            "sub": user.email,
            "scopes": form_data.scopes,
        }
    )

    return Token(access_token=access_token)


@router.get(
    "/me/",
    response_model=UserPublic,

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
        UserPublic: The current authenticated user.
    """
    return current_user


@router.post(
    "/sign-up",
    response_model=UserPublic,

    summary="Sign up a new user",
    response_description="Successful Response with the new user",
)
async def sign_up(
    user: Annotated[
        UserCreate,
        Form(
            title="User to create",
            description="The user to be created",
            openapi_examples=openapi_examples_UserCreate,
            media_type="multipart/form-data"
        )
    ],
    session: SessionDependency,
) -> User:
    """
    Endpoint to sign up a new user.

    This endpoint allows users to create a new account by providing the necessary
    information.

    \f

    Args:
        user (UserCreate): The user information to create a new account.
        session (SessionDependency): The database session dependency.

    Returns:
        UserPublic: The newly created user.

    Raises:
        HTTPException: If the password validation fails.
    """
    validate_password(user.password)

    hashed_password: bytes = get_password_hash(user.password)

    image_uuid: UUID = await save_user_image(user.image)

    extra_data: dict[str, bytes | UUID] = {
        "hashed_password": hashed_password,
        "image_uuid": image_uuid,
    }

    db_user: User = User.model_validate(user, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@router.post(
    "/obtain-users-by-image",
    response_model=list[UserPublic],
    dependencies=[Security(get_current_active_user, scopes=[Scopes.ADMIN])],

    summary="Get users by image provided",
    response_description="Successful Response with a list of users found that are similar to the person in the image",
)
async def obtain_user_by_image(
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
    Endpoint to obtain users by image.

    This endpoint allows users to find registered users by providing an image.
    The image is compared against the database to find similar users.

    \f

    Args:
        image (UploadFile): The image of a registered user.
        session (SessionDependency): The database session dependency.

    Returns:
        list[User]: A list of users found that are similar to the person in the image.

    Raises:
        HTTPException: If no users are found in the images database or the main database.
    """
    async def delete_temp_image(temp_image_path: Path):
        if temp_image_path.exists():
            temp_image_path.unlink()

    temp_image_uuid: UUID = await save_user_image(image, folder="temp_imgs")
    temp_image_path: Path = Path(
        "./data/temp_imgs"
    ) / f"{temp_image_uuid.hex}.png"

    images_df = DeepFace.find(  # type: ignore
        img_path=str(temp_image_path),
        db_path=str(Path("./data/imgs")),
        model_name="Facenet512",
        detector_backend="yunet",
    )

    if len(images_df[0]) < 1:
        await delete_temp_image(temp_image_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in images database",
        )

    users: list[User | None] = [
        session.exec(
            select(User).
            where(
                User.image_uuid == UUID(Path(img).stem)  # type: ignore
            )
        ).first()
        for img in images_df[0]['identity']  # type: ignore
    ]

    if not all(users):
        await delete_temp_image(temp_image_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database",
        )

    await delete_temp_image(temp_image_path)

    return users  # type: ignore


@router.get(
    "/promote-to-admin/{user_id}",
    response_model=UserPublic,
    dependencies=[Security(get_current_active_user, scopes=[Scopes.ADMIN])],

    summary="Promote a user to admin",
    response_description="Successful Response with the promoted user",
)
async def promote_to_admin(
    user_id: int,
    session: SessionDependency,
) -> User:
    """
    Endpoint to promote a user to admin.

    This endpoint allows an admin to promote an assistant user to an admin role.

    \f

    Args:
        user_id (int): The ID of the user to be promoted.
        session (SessionDependency): The database session dependency.

    Returns:
        UserPublic: The promoted user.

    Raises:
        HTTPException: If the user is not found or is already an admin.
    """

    if not (user := session.get(User, user_id)):
        raise HTTPException404UserNotFound

    if user.role == Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an admin",
        )

    user.role = Role.ADMIN
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@router.delete(
    "/delete/{user_id}",
    response_model=UserPublic,
    dependencies=[Security(get_current_active_user, scopes=[Scopes.ADMIN])],

    summary="Delete a user",
    response_description="Successful Response with the deleted user",
)
async def delete_user(
    user_id: int,
    session: SessionDependency,
) -> User:
    """
    Endpoint to delete a user.

    This endpoint allows an admin to delete a user by their ID.

    \f

    Args:
        user_id (int): The ID of the user to be deleted.
        session (SessionDependency): The database session dependency.

    Returns:
        UserPublic: The deleted user.

    Raises:
        HTTPException: If the user is not found.
    """
    if not (user := session.get(User, user_id)):
        raise HTTPException404UserNotFound

    session.delete(user)
    session.commit()

    return user


@router.get(
    "/{user_id}",
    response_model=UserPublic,
    dependencies=[Security(get_current_active_user, scopes=[Scopes.ADMIN])],

    summary="Get a user by ID",
    response_description="Successful Response with the user",
)
async def get_user_by_id(
    user_id: int,
    session: SessionDependency,
) -> User:
    """
    Endpoint to get a user by ID.

    This endpoint allows an admin to retrieve a user by their ID.

    \f

    Args:
        user_id (int): The ID of the user to be retrieved.
        session (SessionDependency): The database session dependency.

    Returns:
        UserPublic: The retrieved user.

    Raises:
        HTTPException: If the user is not found.
    """
    if not (user := session.get(User, user_id)):
        raise HTTPException404UserNotFound

    return user
# endregion
