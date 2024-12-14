"""
This module defines the tags used in the API for grouping operations.
"""

from enum import Enum
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


class Tags(Enum):
    """
    Enum for the tags used in the API.
    """
    users = "users"
# endregion


# region metadata
tags_metadata: list[TagMetadata] = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
]
# endregion
