"""
Defines roles for the API.
"""

from enum import StrEnum, auto

from api.models.Scopes import Scopes


class Role(StrEnum):
    """
    Enum for user roles.

    Represents the different roles that can be assigned to a user in the API.
    """
    ASSISTANT = auto()
    ADMIN = auto()
    STAFF = auto()

    def get_allowed_scopes(self) -> set[Scopes]:
        """
        Get the allowed scopes for the role.

        Returns:
            set[str]: A list of allowed scopes for the role.
        """
        role_scopes: dict[Role, set[Scopes]] = {
            Role.ASSISTANT: {Scopes.USER, Scopes.ASSISTANT},
            Role.ADMIN: {Scopes.USER, Scopes.ASSISTANT, Scopes.ORGANIZER},
            Role.STAFF: {Scopes.STAFF}
        }
        return role_scopes.get(self, set())
