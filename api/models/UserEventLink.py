"""
This module contains SQLModel models for linking users and events.
"""

from sqlmodel import Field, Relationship, SQLModel  # type: ignore

from api.models.Event import Event
from api.models.User import User


class UserEventLink(SQLModel, table=True):
    """
    UserEventLink model.

    Represents a link between a user and an event in the database. Used for saving and retrieving link data from the database.
    """
    user_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        primary_key=True,

        title="User ID",
        description="The ID of the user that is linked to the event",
    )
    event_id: int | None = Field(
        default=None,
        foreign_key="event.id",
        primary_key=True,

        title="Event ID",
        description="The ID of the event that is linked to the user",
    )
    attended: bool = Field(
        default=False,

        title="Attendance of the user",
        description="Field to indicate if the user attended the event",
    )

    user: User = Relationship(back_populates="event_links")
    event: Event = Relationship(back_populates="user_links")
