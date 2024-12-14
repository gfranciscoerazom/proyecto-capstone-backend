"""
This module contains the database engine.
"""

from sqlalchemy import Engine
from sqlmodel import create_engine

from api.settings.config import settings

# region settings
connect_args = {"check_same_thread": False}
# endregion

# region engine
engine: Engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    connect_args=connect_args
)
# endregion
