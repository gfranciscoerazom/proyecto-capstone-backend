"""
This module contains SQLModel models for event management.
"""

from datetime import date

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel  # type: ignore

if TYPE_CHECKING:
    from api.models.UserEventLink import UserEventLink

# if TYPE_CHECKING:
#     from api.models.User import User


class EventBase(SQLModel):
    """
    Base class for the Event model.

    Contains the common fields for the Event model. Used as a base class for the rest of the Event models.
    """
    name: str = Field(
        title="Event Name",
        description="The name of the event.",
    )
    description: str = Field(
        title="Event Description",
        description="A brief description of the event.",
    )
    start_date: date = Field(
        title="Start Date",
        description="The date when the event starts.",
    )
    end_date: date = Field(
        title="End Date",
        description="The date when the event ends.",
    )


class Event(EventBase, table=True):
    """
    Event model.

    Represents an event in the database. Used for saving and retrieving event data from the database.
    """
    id: int | None = Field(
        default=None,
        primary_key=True,

        title="Event ID",
        description="The unique identifier of the event.",
    )
    user_links: list["UserEventLink"] = Relationship(back_populates="event")


class EventPublic(EventBase):
    """
    Public Event model.

    Represents an event in the API. Used for returning event data to the client.
    """
    id: int = Field(
        title="Event ID",
        description="The unique identifier of the event.",
    )


class EventCreate(EventBase):
    """
    Event Create model.

    Represents an event to be created in the API. Used for receiving event data from the client.
    """
    pass


class EventUpdate(SQLModel):
    """
    Event Update model.

    Represents an event to be updated in the API. Used for receiving event data from the client.
    """
    name: str | None = Field(
        default=None,
        title="Event Name",
        description="The name of the event.",
    )
    description: str | None = Field(
        default=None,
        title="Event Description",
        description="A brief description of the event.",
    )
    start_date: date | None = Field(
        default=None,
        title="Start Date",
        description="The date when the event starts.",
    )
    end_date: date | None = Field(
        default=None,
        title="End Date",
        description="The date when the event ends.",
    )
