"""
This module contains pydantic models for tokens and token data.
"""

from pydantic import BaseModel, Field


# region classes
class Token(BaseModel):
    """
    Token model.

    Represents the token to be used for authentication. Used to return the token to the user.
    """
    access_token: str = Field(
        title="Access Token",
        description="The access token to be used for authentication.",
    )
    token_type: str = Field(
        default="bearer",

        title="Token Type",
        description="The type of token. This should always be 'bearer'.",
    )


class TokenData(BaseModel):
    """
    Token Data model.

    Represents the data stored in the token. Used to return the data to the user.
    """
    username: str | None = Field(
        default=None,

        title="Username",
        description="The username of the user.",
    )
    scopes: list[str] = Field(
        default=[],

        title="List of Scopes (Roles)",
        description="The list of scopes (roles) assigned to the user.",
    )
# endregion
