from enum import StrEnum, auto


class TypeCapacity(StrEnum):
    """
    Enum for type capacity.

    Represents the different types of capacity that can be assigned in the API.
    """
    LIMIT_OF_SPACES = auto()
    SITE_CAPACITY = auto()
