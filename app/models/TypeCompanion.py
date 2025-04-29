from enum import StrEnum, auto


class TypeCompanion(StrEnum):
    """Enum to represent the type of companion.

    :var ZERO_GRADE: Representation of the zero grade companion. This means
    that the companion is the user itself.
    :vartype ZERO_GRADE: str

    :var FIRST_GRADE: Representation of the first grade companion. This means
    that the companion is a father or a mother.
    :vartype FIRST_GRADE: str

    :var SECOND_GRADE: Representation of the second grade companion. This means
    that the companion is a brother or a sister.
    :vartype SECOND_GRADE: str

    :var THIRD_GRADE: Representation of the third grade companion. This means
    that the companion is a cousin or a friend.
    :vartype THIRD_GRADE: str"""
    ZERO_GRADE = auto()
    FIRST_GRADE = auto()
    SECOND_GRADE = auto()
    THIRD_GRADE = auto()
