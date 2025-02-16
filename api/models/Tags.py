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
    users = auto()
    events = auto()
    assistants = auto()
# endregion


# region metadata
tags_metadata: list[TagMetadata] = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "events",
        "description": "Operations with events.",
    },
    {
        "name": "assistants",
        "description": "Operations with assistants.",
    },
]
# endregion
