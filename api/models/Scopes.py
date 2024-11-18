from enum import StrEnum, auto


# region classes
class Scopes(StrEnum):
    """
    Scopes for the API.

    Represents the different scopes that can be assigned to a user in the API.
    """
    ADMIN = auto()
    ASSISTANT = auto()
# endregion


# region variables
scopes: dict[Scopes, str] = {
    Scopes.ADMIN: "User with admin privileges",
    Scopes.ASSISTANT: "User with assistant privileges",
}
# endregion
