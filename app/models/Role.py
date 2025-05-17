"""
Defines roles for the API.
"""

from enum import StrEnum, auto

from app.models.Scopes import Scopes


class Role(StrEnum):
    """
    Enum for user roles.

    Represents the different roles that can be assigned to a user in the API.
    """
    ASSISTANT = auto()
    STAFF = auto()
    ORGANIZER = auto()

    def get_scopes(self) -> set[Scopes]:
        """
        Get the allowed scopes for the role.

        Returns:
            set[str]: A list of allowed scopes for the role.
        """
        role_scopes: dict[Role, set[Scopes]] = {
            Role.ASSISTANT: {Scopes.ASSISTANT},
            Role.STAFF: {Scopes.STAFF},
            Role.ORGANIZER: {Scopes.ORGANIZER}
        }
        return role_scopes.get(self, set())
