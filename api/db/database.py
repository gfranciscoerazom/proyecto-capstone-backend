import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any, Literal, Optional
from uuid import UUID

import jwt
from deepface import DeepFace  # type: ignore
from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.security import SecurityScopes
from pydantic import EmailStr, ValidationError
from sqlalchemy import Engine
from sqlmodel import (Field, Relationship, Session, SQLModel,  # type: ignore
                      create_engine, select)

from api.models.Gender import Gender
from api.models.Role import Role
from api.models.Token import TokenData
from api.models.TypeId import TypeId
from api.security.security import oauth2_scheme, verify_password
from api.settings.config import settings

# region settings
connect_args = {"check_same_thread": False}
# endregion

# region engine
engine: Engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    connect_args=connect_args
)
# endregion

# Función para obtener la hora de Quito


def get_quito_time() -> datetime:
    """Función para obtener la hora actual en Quito, Ecuador."""
    quito_timezone = timezone(timedelta(hours=-5))
    return datetime.now(quito_timezone)


# region User

class UserBase(SQLModel):
    """Base class for User models."""
    email: EmailStr = Field(
        index=True,
        unique=True,

        title="Email address",
        description="User email address (used for login)",
    )
    first_name: str = Field(
        min_length=2,

        title="First Name",
        description="User first name",
    )
    last_name: str = Field(
        min_length=2,

        title="Last Name",
        description="User last name",
    )
    role: Role = Field(
        default=Role.ASSISTANT,

        title="Role",
        description="User role (organizer/staff/assistant)",
    )


class User(UserBase, table=True):
    """User database model."""
    id: int | None = Field(
        default=None,
        primary_key=True,

        title="User ID",
        description="The user's unique identifier",
    )
    hashed_password: bytes = Field(
        title="Hashed Password",
        description="The hashed password of the user. Used for authentication.",
    )
    created_at: datetime = Field(
        default_factory=get_quito_time,

        title="Date and time of creation",
        description="User creation date and time, in Quito timezone",
    )
    is_active: bool = Field(
        default=True,

        title="Flag for active status",
        description="Field to determine if the user is active or not",
    )

    assistant: Optional["Assistant"] = Relationship(
        back_populates="user",
    )  # ✅
    organized_events: list["Event"] = Relationship(
        back_populates="organizer",
    )  # ✅


class UserPublic(UserBase):
    """Public User model for API responses."""
    id: int = Field(
        title="User ID",
        description="The user's unique identifier",
    )
    created_at: datetime = Field(
        title="Date and time of creation",
        description="User creation date and time, in Quito timezone",
    )
    is_active: bool = Field(
        title="Flag for active status",
        description="Field to determine if the user is active or not",
    )


class UserCreate(UserBase):
    """User create model for API requests."""
    password: str = Field(
        regex='^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,}$',

        title="Password",
        description="User password"
    )


class UserUpdate(SQLModel):
    """User update model for API requests."""
    email: EmailStr | None = Field(
        default=None,
        index=True,

        title="Email",
        description="User email"
    )
    first_name: str | None = Field(
        default=None,

        title="First Name",
        description="User first name"
    )
    last_name: str | None = Field(
        default=None,

        title="Last Name",
        description="User last name"
    )
    password: str | None = Field(
        default=None,

        title="Password",
        description="User password"
    )
    role: Role | None = Field(
        default=None,

        title="Role",
        description="User role (organizer/staff/assistant)"
    )
    is_active: bool | None = Field(
        default=None,

        title="Is Active",
        description="User active status"
    )


# region Assistant

class AssistantBase(SQLModel):
    """Base class for Assistant models."""
    id_number: str = Field(
        unique=True,
        index=True,
        min_length=8,
        max_length=10,

        title="ID Number",
        description="Assistant ID number (cédula/pasaporte)"
    )
    id_number_type: TypeId = Field(
        default=TypeId.CEDULA,

        title="ID Number Type",
        description="Type of the ID (cédula/pasaporte)"
    )
    phone: str = Field(
        min_length=10,
        max_length=10,

        title="Phone",
        description="Assistant phone number (10 digits)"
    )
    gender: Gender = Field(
        title="Gender",
        description="Assistant gender (Male/Female/Other)"
    )
    date_of_birth: date = Field(
        title="Date of Birth",
        description="Assistant date of birth"
    )
    accepted_terms: bool = Field(
        title="Accepted Terms",
        description="Terms acceptance status"
    )


class Assistant(AssistantBase, table=True):
    """Assistant database model."""
    user_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        primary_key=True,

        title="User ID",
        description="Foreign key to User table"
    )
    image_uuid: UUID = Field(
        unique=True,
        index=True,

        title="Face Photo",
        description="UUID of assistant face photo"
    )

    user: User = Relationship(
        back_populates="assistant"
    )  # ✅

    registrations: list["Registration"] = Relationship(
        back_populates="assistant"
    )


class AssistantPublic(AssistantBase):
    """Public Assistant model for API responses."""
    user_id: int = Field(
        title="User ID",
        description="Foreign key to User table"
    )
    image_uuid: UUID = Field(
        title="Face Photo",
        description="UUID of assistant face photo"
    )


class AssistantCreate(AssistantBase):
    """Assistant create model for API requests."""
    image: UploadFile = Field(
        title="Face Photo",
        description="Assistant face photo"
    )


class AssistantUpdate(SQLModel):
    """Assistant update model for API requests."""
    id_number: str | None = Field(
        default=None,
        min_length=8,
        max_length=10,

        title="ID Number",
        description="Assistant ID number"
    )
    id_number_type: TypeId | None = Field(
        default=None,

        title="ID Number Type",
        description="Type of the ID (cédula/pasaporte)"
    )
    phone: str | None = Field(
        default=None,
        min_length=10,
        max_length=10,

        title="Phone",
        description="Assistant phone number"
    )
    gender: Gender | None = Field(
        default=None,

        title="Gender",
        description="Assistant gender (Female/Male/Other)"
    )
    date_of_birth: date | None = Field(
        default=None,

        title="Date of Birth",
        description="Assistant date of birth"
    )
    accepted_terms: bool | None = Field(
        default=None,

        title="Accepted Terms",
        description="Terms acceptance status"
    )
    image: UploadFile | None = Field(
        default=None,

        title="Face Photo",
        description="Assistant face photo"
    )


class UserAssistantPublic(UserPublic):
    assistant: AssistantPublic


class UserAssistantCreate(UserCreate, AssistantCreate):
    def get_user(self) -> UserCreate:
        return UserCreate(
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            password=self.password
        )

    def get_assistant(self) -> AssistantCreate:
        return AssistantCreate(
            id_number=self.id_number,
            id_number_type=self.id_number_type,
            phone=self.phone,
            gender=self.gender,
            date_of_birth=self.date_of_birth,
            accepted_terms=self.accepted_terms,
            image=self.image,
        )

# region Event


class EventBase(SQLModel):
    """Base class for Event models."""
    name: str = Field(
        unique=True,

        title="Name",
        description="Event name"
    )
    description: str = Field(
        title="Description",
        description="Event description"
    )
    location: str = Field(
        title="Location",
        description="Event location"
    )
    maps_link: str = Field(
        regex="^https://maps\\.app\\.goo\\.gl/.*$",

        title="Maps Link",
        description="Event maps link (https://maps.app.goo.gl/)"
    )
    max_capacity: int | None = Field(
        default=None,
        ge=1,

        title="Max Capacity",
        description="Event maximum capacity"
    )
    venue_capacity: int | None = Field(
        default=None,
        ge=1,

        title="Venue Capacity",
        description="Event venue capacity"
    )
    organizer_id: int = Field(
        foreign_key="user.id",

        title="Organizer ID",
        description="Foreign key to User table (organizer)"
    )


class Event(EventBase, table=True):
    """Event database model."""
    created_at: datetime = Field(
        default_factory=get_quito_time,

        title="Created At",
        description="Event creation date and time, in Quito timezone"
    )
    promo_photo: str = Field(
        unique=True,

        title="Promo Photo",
        description="Name of promo photo"
    )
    is_cancelled: bool = Field(
        default=False,

        title="Is Cancelled",
        description="Event cancellation status"
    )
    id: int | None = Field(
        primary_key=True,
        default=None,

        title="ID",
        description="Event ID"
    )
    is_published: bool = Field(
        default=False,

        title="Is Published",
        description="Event published status"
    )

    organizer: User = Relationship(
        back_populates="organized_events"
    )  # ✅
    event_dates: list["EventDate"] = Relationship(
        back_populates="event"
    )  # ✅
    registrations: list["Registration"] = Relationship(
        back_populates="event"
    )


class EventPublic(EventBase):
    """Public Event model for API responses."""
    created_at: datetime = Field(
        title="Created At",
        description="Event creation date and time, in Quito timezone"
    )
    is_cancelled: bool = Field(
        title="Is Cancelled",
        description="Event cancellation status"
    )
    id: int = Field(
        title="ID",
        description="Event ID"
    )
    is_published: bool = Field(
        title="Is Published",
        description="Event published status"
    )
    # TODO: Foto promo


class EventCreate(EventBase):
    """Event create model for API requests."""
    promo_photo: UploadFile = Field(
        title="Promo Photo",
        description="Name of promo photo"
    )


class EventUpdate(SQLModel):
    """Event update model for API requests."""
    name: str | None = Field(
        default=None, title="Name", description="Event name")
    description: str | None = Field(
        default=None, title="Description", description="Event description")
    location: str | None = Field(
        default=None, title="Location", description="Event location")
    maps_link: str | None = Field(
        default=None, title="Maps Link", description="Event maps link (https://maps.app.goo.gl/)")
    max_capacity: int | None = Field(
        default=None, title="Max Capacity", description="Event maximum capacity")
    venue_capacity: int | None = Field(
        default=None, title="Venue Capacity", description="Event venue capacity")
    promo_photo: str | None = Field(
        default=None, title="Promo Photo", description="Path to event promo photo")
    is_cancelled: bool | None = Field(
        default=None, title="Is Cancelled", description="Event cancellation status")
    organizer_id: int | None = Field(
        default=None, title="Organizer ID", description="Organizer User ID")


# region EventDate


class EventDateBase(SQLModel):
    """Base class for EventDate models."""
    day_date: date = Field(
        title="Date",
        description="Event date"
    )
    start_time: time = Field(
        title="Start Time",
        description="Event start time"
    )
    end_time: time = Field(
        title="End Time",
        description="Event end time"
    )
    event_id: int = Field(
        foreign_key="event.id",
        index=True,

        title="Event ID",
        description="Foreign key to Event table"
    )


class EventDate(EventDateBase, table=True):
    """EventDate database model."""
    id: int | None = Field(
        default=None,
        primary_key=True,

        title="ID",
        description="Event Date ID"
    )

    event: Event = Relationship(
        back_populates="event_dates"
    )  # ✅


class EventDatePublic(EventDateBase):
    """Public EventDate model for API responses."""
    id: int = Field(
        title="ID",
        description="Event Date ID"
    )


class EventDateCreate(EventDateBase):
    """EventDate create model for API requests."""
    pass


class EventDateUpdate(SQLModel):
    """EventDate update model for API requests."""
    day_date: date | None = Field(
        default=None, title="Date", description="Event date")
    start_time: time | None = Field(
        default=None, title="Start Time", description="Event start time")
    end_time: time | None = Field(
        default=None, title="End Time", description="Event end time")
    event_id: int | None = Field(
        default=None, title="Event ID", description="Event ID")


# region Registration

class GuestAssociation(SQLModel, table=True):
    """Association table for many-to-many relationship between Registrations."""
    registration_id: int = Field(
        foreign_key="registration.id",
        primary_key=True,
        title="Registration ID",
        description="Foreign key to Registration table"
    )
    guest_id: int = Field(
        foreign_key="registration.id",
        primary_key=True,
        title="Guest ID",
        description="Foreign key to Registration table"
    )


class RegistrationBase(SQLModel):
    """Base class for Registration models."""
    event_id: int = Field(
        foreign_key="event.id",
        title="Event ID",
        description="Foreign key to Event table"
    )
    assistant_id: int = Field(
        foreign_key="assistant.user_id",
        title="Assistant ID",
        description="Foreign key to Assistant table"
    )


class Registration(RegistrationBase, table=True):
    """Registration database model."""
    id: int | None = Field(
        default=None,
        primary_key=True,
        title="ID",
        description="Registration ID"
    )
    created_at: datetime = Field(
        default_factory=get_quito_time,
        title="Created At",
        description="Registration creation date and time, in Quito timezone"
    )
    attended: bool = Field(
        default=False,
        title="Attended",
        description="Attendance status"
    )
    attendance_time: datetime | None = Field(
        default=None,

        title="Attendance Time",
        description="Time of attendance"
    )
    reaction: int = Field(
        default=0,
        title="Reaction",
        description="User reaction (1: Liked, -1: Disliked, 0: No reaction)"
    )
    reaction_date: datetime | None = Field(
        default=None,
        title="Reaction Date",
        description="Date of reaction"
    )

    event: Event = Relationship(
        back_populates="registrations"
    )
    assistant: Assistant = Relationship(
        back_populates="registrations"
    )
    guest_registrations: list["Registration"] = Relationship(
        back_populates="guest_of_registration",
        link_model=GuestAssociation,
        sa_relationship_kwargs={
            "primaryjoin": "Registration.id==GuestAssociation.registration_id",
            "secondaryjoin": "Registration.id==GuestAssociation.guest_id",
            "foreign_keys": "[GuestAssociation.registration_id, GuestAssociation.guest_id]"
        }
    )
    guest_of_registration: list["Registration"] = Relationship(
        back_populates="guest_registrations",
        link_model=GuestAssociation,
        sa_relationship_kwargs={
            "primaryjoin": "Registration.id==GuestAssociation.guest_id",
            "secondaryjoin": "Registration.id==GuestAssociation.registration_id",
            "foreign_keys": "[GuestAssociation.guest_id, GuestAssociation.registration_id]"
        }
    )


class RegistrationPublic(RegistrationBase):
    id: int = Field(
        title="ID",
        description="Registration ID"
    )
    created_at: datetime = Field(
        title="Created At",
        description="Registration creation date and time, in Quito timezone"
    )
    attended: bool = Field(
        title="Attended",
        description="Attendance status"
    )
    attendance_time: datetime | None = Field(
        title="Attendance Time",
        description="Time of attendance"
    )
    reaction: int = Field(
        title="Reaction",
        description="User reaction (1: Liked, -1: Disliked, 0: No reaction)"
    )
    reaction_date: datetime | None = Field(
        title="Reaction Date",
        description="Date of reaction"
    )


class RegistrationCreate(RegistrationBase):
    """Registration create model for API requests."""
    pass


class RegistrationUpdate(SQLModel):
    """Registration update model for API requests."""
    registration_date: datetime | None = Field(
        default=None,
        title="Registration Date",
        description="Date of registration"
    )
    attended: bool | None = Field(
        default=None,
        title="Attended",
        description="Attendance status"
    )
    reaction: int | None = Field(
        default=None,
        title="Reaction",
        description="User reaction (1: Liked, -1: Disliked, 0: No reaction)"
    )
    reaction_date: datetime | None = Field(
        default=None,
        title="Reaction Date",
        description="Date of reaction"
    )
    event_id: int | None = Field(
        default=None,
        title="Event ID",
        description="Event ID"
    )
    assistant_id: int | None = Field(
        default=None,
        title="Assistant ID",
        description="Assistant ID"
    )
    is_guest_of: int | None = Field(
        default=None,
        title="Guest Of ID",
        description="Guest Of Registration ID"
    )


def create_db_and_tables() -> None:
    """Creates database tables if they don't exist."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session


def get_user(
    email: EmailStr | None = None,
    user_id: int | None = None
) -> User | None:
    """Retrieve a user by email or ID."""
    if not email and not user_id:
        return None

    with Session(engine) as session:
        if email:
            return session.exec(select(User).where(User.email == email)).first()
        if user_id:
            return session.get(User, user_id)
    return None


def authenticate_user(email: EmailStr, password: str) -> User | Literal[False]:
    """Authenticates user by email and password."""
    if not (user := get_user(email=email)):
        return False
    return user if verify_password(password, user.hashed_password) else False


def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """Dependency to get current user from token."""
    authenticate_value: str = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload: dict[str, Any] = jwt.decode(  # type: ignore
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if not (username := payload.get("sub")):
            raise credentials_exception

        token_scopes: list[str] = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except (jwt.InvalidTokenError, ValidationError):
        raise credentials_exception

    if not (user := get_user(email=token_data.username)):
        raise credentials_exception

    if not all(scope in token_data.scopes for scope in security_scopes.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": authenticate_value},
        )
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency to get current active user."""
    if not current_user.is_active:  # Changed to .is_active
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def is_single_person(image_path: Path) -> bool:
    """Checks if image contains a single person."""
    try:
        face_objs = DeepFace.extract_faces(  # type: ignore
            img_path=str(image_path),
            detector_backend="yunet",
            align=True,
        )
    except ValueError as e:
        if "Face could not be detected" in str(e):
            return False
        raise e
    return len(face_objs) == 1


async def save_user_image(image: UploadFile, folder: str = "imgs") -> UUID:
    """Saves user image and returns UUID."""
    image_uuid: UUID = uuid.uuid4()
    image_path: Path = Path(
        f"./data/{folder}/{image_uuid.hex}.png"
    )
    image_path.parent.mkdir(parents=True, exist_ok=True)

    with image_path.open("wb") as image_file:
        image_file.write(await image.read())

    if not is_single_person(image_path):
        if image_path.exists():
            image_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The image must contain exactly one person",
        )
    return image_uuid


# region dependencies
SessionDependency = Annotated[Session, Depends(get_session)]
# endregion
