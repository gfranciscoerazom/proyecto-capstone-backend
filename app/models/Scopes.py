"""
Defines scopes for the API.
"""

from enum import StrEnum, auto


# region classes
class Scopes(StrEnum):
    """
    Scopes for the API.

    Represents the different scopes that can be assigned to a user in the API.
    """
    ORGANIZER = auto()
    ASSISTANT = auto()
    STAFF = auto()
# endregion


# region variables
scopes: dict[Scopes, str] = {
    Scopes.ORGANIZER: "User with organizer privileges",
    Scopes.ASSISTANT: "User with assistant privileges",
    Scopes.STAFF: "User with staff privileges",
}
# endregion
