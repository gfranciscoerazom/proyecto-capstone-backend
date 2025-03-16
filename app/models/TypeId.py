from enum import StrEnum, auto


class TypeId(StrEnum):
    """
    Enum for user roles.

    Represents the different roles that can be assigned to a user in the API.
    """
    CEDULA = auto()
    PASSPORT = auto()
