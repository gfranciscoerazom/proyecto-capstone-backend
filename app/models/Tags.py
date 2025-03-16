"""
This module defines the tags used in the API for grouping operations.
"""

from enum import StrEnum, auto
from typing import NotRequired, TypedDict

# region classes
ExternalDocs = TypedDict(
    "ExternalDocs",
    {
        "description": str,
        "url": str
    },
)

TagMetadata = TypedDict(
    "TagMetadata",
    {
        "name": str,
        "description": str,
        "externalDocs": NotRequired[ExternalDocs]
    },
)


class Tags(StrEnum):
    """
    Enum for the tags used in the API.
    """
    events = auto()
    assistants = auto()
    staff = auto()
    organizer = auto()
# endregion


# region metadata
tags_metadata: list[TagMetadata] = [
    {
        "name": Tags.events,
        "description": "Operations with events.",
    },
    {
        "name": Tags.assistants,
        "description": "Operations with assistants.",
    },
    {
        "name": Tags.organizer,
        "description": "Operations with organizers.",
    },
    {
        "name": Tags.staff,
        "description": "Operations with staff.",
    },
]
# endregion
