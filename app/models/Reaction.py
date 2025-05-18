from enum import StrEnum, auto


class Reaction(StrEnum):
    DISLIKE = auto()
    NO_REACTION = auto()
    LIKE = auto()
