from datetime import date, datetime, time
from typing import Annotated, Any, Literal, Self
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.security import SecurityScopes
from pydantic import (AfterValidator, EmailStr, PositiveInt, ValidationError,
                      field_validator, model_validator)
from sqlalchemy import Engine, Text
from sqlmodel import (Field, Relationship, Session, SQLModel,  # type: ignore
                      create_engine, select)

from app.db.datatypes import (BeforeTodayDate, GoogleMapsURL, Password,
                              PhoneNumber, TermsAndConditions, UpperStr)
from app.helpers.dateAndTime import get_quito_time
from app.helpers.validations import (is_valid_ecuadorian_id,
                                     is_valid_ecuadorian_passport_number)
from app.models.Gender import Gender
from app.models.Reaction import Reaction
from app.models.Role import Role
from app.models.Token import TokenData
from app.models.TypeCapacity import TypeCapacity
from app.models.TypeId import TypeId
from app.security.security import oauth2_scheme, verify_password
from app.settings.config import settings

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


# region Assistant

class AssistantBase(SQLModel):
    """Base class for Assistant models."""
    id_number: UpperStr = Field(
        unique=True,
        index=True,
        min_length=8,
        max_length=10,

        title="ID Number",
        description="Assistant ID number (cédula/pasaporte)"
    )
    id_number_type: TypeId = Field(
        title="ID Number Type",
        description="Type of the ID (cédula/pasaporte)"
    )
    phone: PhoneNumber = Field(
        title="Phone",
        description="Assistant phone number (10 digits)"
    )
    gender: Gender = Field(
        title="Gender",
        description="Assistant gender (Male/Female/Other)"
    )
    date_of_birth: BeforeTodayDate = Field(
        title="Date of Birth",
        description="Assistant date of birth"
    )
    accepted_terms: TermsAndConditions = Field(
        title="Accepted Terms",
        description="Terms acceptance status"
    )

    @model_validator(mode="after")
    def validate_id_number(self) -> Self:
        match self.id_number_type:
            case TypeId.CEDULA:
                if not is_valid_ecuadorian_id(self.id_number):
                    raise ValueError("Invalid Ecuadorian ID number")
            case TypeId.PASSPORT:
                if not is_valid_ecuadorian_passport_number(self.id_number):
                    raise ValueError("Invalid Ecuadorian passport number")

        return self


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

    user: "User" = Relationship(
        back_populates="assistant"
    )
    registrations_as_companion: list["Registration"] = Relationship(
        back_populates="companion",
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
    phone: PhoneNumber | None = Field(
        default=None,

        title="Phone",
        description="Assistant phone number"
    )
    gender: Gender | None = Field(
        default=None,

        title="Gender",
        description="Assistant gender (Female/Male/Other)"
    )
    date_of_birth: BeforeTodayDate | None = Field(
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


# region User

class UserBase(SQLModel):
    """
    Base class for User models.

    This class is used to define the common attributes of the Users models.
    """
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
    role: Role = Field(
        title="Role",
        description="User role (organizer/staff/assistant)",
    )

    assistant: Assistant | None = Relationship(
        back_populates="user",
    )
    organized_events: list["Event"] = Relationship(
        back_populates="organizer",
    )
    registrations_as_assistant: list["Registration"] = Relationship(
        back_populates="assistant",
    )

    @model_validator(mode="after")
    def validate_email_by_role(self) -> Self:
        """Validate that if the role is assistant, the email is not from the UDLA domain. (udla.edu.ec) and if the role is organizer or staff, the email is from the UDLA domain."""
        match self.role:
            case Role.ASSISTANT:
                if self.email.endswith("udla.edu.ec"):
                    raise ValueError(
                        "Assistant email cannot be from UDLA domain")
            case Role.ORGANIZER | Role.STAFF:
                if not self.email.endswith("udla.edu.ec"):
                    raise ValueError(
                        "Organizer or staff email must be from UDLA domain")

        return self


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
    role: Role = Field(
        title="Role",
        description="User role (organizer/staff/assistant)",
    )


class UserCreate(UserBase):
    """User create model for API requests."""
    password: Password = Field(
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


class UserAssistantPublic(UserPublic):
    assistant: AssistantPublic


class UserAssistantCreate(UserCreate, AssistantCreate):
    def get_user(self) -> UserCreate:
        return UserCreate.model_validate(self)

    def get_assistant(self) -> AssistantCreate:
        return AssistantCreate.model_validate(self)

# region Event


class EventBase(SQLModel):
    """Base class for Event models."""
    name: str = Field(
        unique=True,

        title="Name",
        description="Event name"
    )
    description: str = Field(
        sa_type=Text,
        title="Description",
        description="Event description"
    )
    location: str = Field(
        title="Location",
        description="Event location"
    )
    maps_link: GoogleMapsURL = Field(
        title="Maps Link",
        description="Event maps link (https://maps.app.goo.gl/)"
    )
    capacity: PositiveInt = Field(
        ge=1,

        title="Max Capacity",
        description="Event maximum capacity"
    )
    capacity_type: TypeCapacity = Field(
        title="Capacity Type",
        description="Type of capacity for the event"
    )


class Event(EventBase, table=True):
    """Event database model."""
    created_at: datetime = Field(
        default_factory=get_quito_time,

        title="Created At",
        description="Event creation date and time, in Quito timezone"
    )
    image_uuid: UUID = Field(
        unique=True,

        title="Event Image",
        description="Path to event image"
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
    organizer_id: int = Field(
        foreign_key="user.id",

        title="Organizer ID",
        description="Foreign key to User table (organizer)"
    )

    organizer: User = Relationship(
        back_populates="organized_events"
    )
    event_dates: list["EventDate"] = Relationship(
        back_populates="event"
    )
    registrations: list["Registration"] = Relationship(
        back_populates="event"
    )

    @field_validator("organizer_id", mode="after")
    @classmethod
    def is_valid_organizer_id(cls, organizer_id: int) -> int:
        if organizer_id < 1:
            raise ValueError("Organizer ID must be greater than 0.")

        with Session(engine) as session:
            if not (
                user := session.exec(
                    select(User).where(User.id == organizer_id)
                ).first()
            ):
                raise ValueError("Organizer not found.")

            if user.role != Role.ORGANIZER:
                raise ValueError("User is not an organizer.")

        return organizer_id


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
    image_uuid: UUID = Field(
        title="Event Image",
        description="Path to event image"
    )
    organizer_id: int = Field(
        title="Organizer ID",
        description="Organizer User ID"
    )


class EventCreate(EventBase):
    """Event create model for API requests."""
    image: UploadFile = Field(
        title="Event Image",
        description="Path to event image"
    )


class EventUpdate(SQLModel):
    """Event update model for API requests."""
    name: str | None = Field(
        default=None, title="Name", description="Event name")
    description: str | None = Field(
        default=None, title="Description", description="Event description")
    location: str | None = Field(
        default=None, title="Location", description="Event location")
    maps_link: GoogleMapsURL | None = Field(
        default=None, title="Maps Link", description="Event maps link (https://maps.app.goo.gl/)")
    max_capacity: int | None = Field(
        default=None, title="Max Capacity", description="Event maximum capacity")
    venue_capacity: int | None = Field(
        default=None, title="Venue Capacity", description="Event venue capacity")
    image: str | None = Field(
        default=None, title="Event Image", description="Path to event image")
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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EventDateBase):
            raise TypeError(
                f"Comparing EventDateBase with {type(other)} is not supported."
            )
        return self.day_date == other.day_date

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, EventDateBase):
            raise TypeError(
                f"Comparing EventDateBase with {type(other)} is not supported."
            )
        return self.day_date != other.day_date

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, EventDateBase):
            raise TypeError(
                f"Comparing EventDateBase with {type(other)} is not supported."
            )
        return self.day_date < other.day_date

    def __le__(self, other: object) -> bool:
        if not isinstance(other, EventDateBase):
            raise TypeError(
                f"Comparing EventDateBase with {type(other)} is not supported."
            )
        return self.day_date <= other.day_date

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, EventDateBase):
            raise TypeError(
                f"Comparing EventDateBase with {type(other)} is not supported."
            )
        return self.day_date > other.day_date

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, EventDateBase):
            raise TypeError(
                f"Comparing EventDateBase with {type(other)} is not supported."
            )
        return self.day_date >= other.day_date

    @model_validator(mode="after")
    def validate_start_time(self) -> Self:
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time.")
        return self


class EventDate(EventDateBase, table=True):
    """EventDate database model."""
    id: int | None = Field(
        default=None,
        primary_key=True,

        title="ID",
        description="Event Date ID"
    )
    event_id: int = Field(
        default=0,
        foreign_key="event.id",
        index=True,

        title="Event ID",
        description="Foreign key to Event table"
    )

    event: Event = Relationship(
        back_populates="event_dates"
    )


class EventDatePublic(EventDateBase):
    """Public EventDate model for API responses."""
    id: int = Field(
        title="ID",
        description="Event Date ID"
    )
    event_id: int = Field(
        title="Event ID",
        description="Foreign key to Event table"
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
    event_name: str | None = Field(
        default=None, title="Event Name", description="Name of the event")
    location: str | None = Field(
        default=None, title="Location", description="Event location")


class EventPublicWithEventDate(EventPublic):
    event_dates: Annotated[
        list[EventDatePublic],
        AfterValidator(lambda x: sorted(x))
    ] = []


# region Registration
class RegistrationBase(SQLModel):
    """Base class for Registration models."""
    event_id: int | None = Field(
        default=None,
        foreign_key="event.id",
        primary_key=True,

        title="Event ID",
        description="Foreign key to Event table"
    )
    assistant_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        primary_key=True,

        title="User ID",
        description="Foreign key to User table"
    )
    companion_id: int | None = Field(
        default=None,
        foreign_key="assistant.user_id",
        primary_key=True,

        title="Companion ID",
        description="Foreign key to Companion table"
    )


class Registration(RegistrationBase, table=True):
    """Registration database model."""
    created_at: datetime = Field(
        default_factory=get_quito_time,

        title="Created At",
        description="Registration creation date and time, in Quito timezone"
    )
    attendance_time: datetime | None = Field(
        default=None,

        title="Attendance Time",
        description="Time of attendance if this value is None, the user did not attend the event"
    )
    reaction: Reaction = Field(
        default=Reaction.NO_REACTION,
        ge=-1,
        le=1,

        title="Reaction",
        description="User reaction (1: Liked, -1: Disliked, 0: No reaction)"
    )
    reaction_date: datetime | None = Field(
        default=None,

        title="Reaction Date",
        description="Date of reaction"
    )
    assistant: User = Relationship(
        back_populates="registrations_as_assistant",
    )
    companion: Assistant = Relationship(
        back_populates="registrations_as_companion",
    )
    event: Event = Relationship(
        back_populates="registrations"
    )


class RegistrationPublic(RegistrationBase):
    created_at: datetime = Field(
        title="Created At",
        description="Registration creation date and time, in Quito timezone"
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


class RegistrationUpdate(SQLModel):
    """Registration update model for API requests."""
    registration_date: datetime | None = Field(
        default=None,
        title="Registration Date",
        description="Date of registration"
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

#####################################################
#
#   Functions
#
#####################################################


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


# region dependencies
SessionDependency = Annotated[Session, Depends(get_session)]
# endregion
