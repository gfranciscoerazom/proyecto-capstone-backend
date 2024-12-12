from functools import lru_cache
from typing import Annotated, Final

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# region classes
class Settings(BaseSettings):
    """
    Settings for the application.

    Settings for the application that are loaded from the environment variables.
    """
    SECRET_KEY: Final[str] = Field(
        title="Secret Key",
        description="Secret key for JWT token",
        examples=[
            "42f2029d884cb2707f9abd7ba591a060ed031d7e99dff1e86bc2f0de665f4b39",
            "b872cd1a34b3cb6122b18466dcd01cae48572b453e03116f79f1ecc276aadb2d",
        ],
        max_length=64,
        min_length=64,
    )
    ALGORITHM: Final[str] = Field(
        title="Algorithm",
        description="Algorithm for JWT token",
        examples=["HS256"],
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = Field(
        title="Access Token Expire Minutes",
        description="Time duration after which the token will expire",
        examples=[30],

        ge=1,
    )
    DATABASE_URL: Final[str] = Field(
        title="Database URL",
        description="URL for the database",
        examples=[
            "sqlite:///this/is/an/example.db",
            "postgresql://user:password@localhost/db",
        ],
    )

    model_config = SettingsConfigDict(env_file="./../../.env")
# endregion


# region functions
@lru_cache
def get_settings() -> Settings:
    """
    Get the settings for the application. This function is cached.

    Returns:
        Settings: The settings for the application.
    """
    return Settings()  # type: ignore
# endregion


# region variables
settings: Settings = get_settings()

settings_dependency = Annotated[Settings, Depends(get_settings)]
# endregion
