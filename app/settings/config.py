"""
This module defines the application's settings using Pydantic's BaseSettings

It centralizes configuration parameters, loading them from environment variables
with the help of `pydantic-settings`. These settings are crucial for various
aspects of the application, including:

- **Security:** Managing the secret key and algorithm for JWT token generation.
- **Database:** Specifying the database connection URL.
- **Token Management:** Defining the token expiration time.

The settings are made accessible throughout the application using FastAPI's
dependency injection system via the `SettingsDependency` variable.

**Key Settings:**

- `SECRET_KEY`: A secret key used for signing JWT tokens. It should be a
   strong, randomly generated string.
- `ALGORITHM`: The algorithm used for signing JWT tokens (e.g., HS256).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: The duration (in minutes) for which access
   tokens are valid.
- `DATABASE_URL`: The connection URL for the database, including the database
   type, credentials, and database name.

This approach ensures that configuration is well-organized, type-safe, and
easily accessible across the application.
"""

from functools import lru_cache
from pathlib import Path
from typing import Final

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# region classes
class Settings(BaseSettings):
    """
    Settings for the application.

    Settings for the application that are loaded from the environment variables.
    """
    ENVIRONMENT: Final[str] = Field(
        title="Environment",
        description="Environment in which the application is running",
        examples=["development", "production"],
    )
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
    EMAIL_SENDER: Final[EmailStr] = Field(
        title="Email Sender",
        description="Email address of the sender",
        examples=["email@gmail.com"],
    )
    EMAIL_APP_PASSWORD: Final[str] = Field(
        title="Email App Password",
        description="App password for the email sender",
        examples=["xxxx xxxx xxxx xxxx"],
    )
    LOGS_TOKEN: Final[str] = Field(
        title="Logs Token",
        description="Token to connect to the system",
        examples=["xxxx_xx_xx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"],
    )
    FACE_RECOGNITION_AI_MODEL: Final[str] = Field(
        title="Face Recognition AI Model",
        description="Model for face recognition",
        examples=["VGG-Face", "Facenet", "Facenet512", "OpenFace", "DeepFace",
                  "DeepID", "ArcFace", "Dlib", "SFace", "GhostFaceNet",
                  "Buffalo_L",],
    )
    FACE_RECOGNITION_AI_THRESHOLD: float | None = Field(
        default=None,
        title="Face Recognition AI Threshold",
        description="Threshold for face recognition",
        examples=[0.5, 0.6, 0.7],
    )

    model_config = SettingsConfigDict(
        env_file=Path.cwd() / ".env",
        env_file_encoding='utf-8',
    )
# endregion


# region functions
@lru_cache
def get_settings() -> Settings:
    """Returns the settings for the application.
    This function uses the `lru_cache` decorator to cache the settings object,
    so that it is only loaded once and reused for subsequent calls.

    :return: Settings object containing the application settings.
    :rtype: Settings
    """
    return Settings()  # type: ignore


def update_settings():
    settings = get_settings()
    settings.__init__()  # type: ignore
# endregion


# region variables
settings: Settings = get_settings()
# endregion
