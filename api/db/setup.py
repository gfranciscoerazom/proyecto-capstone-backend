from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel

from api.db.engine import engine
from api.models.User import User  # type: ignore


# region functions
def create_db_and_tables():
    """
    Create the database and all tables defined in the SQLModel metadata.

    This function initializes the database by creating all the tables
    that are defined in the SQLModel metadata. It uses the `create_all`
    method of the SQLAlchemy engine to perform the creation.

    Returns:
        None
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Creates a new database session and yields it.

    This function uses a context manager to ensure that the session is properly
    closed after use. It is intended to be used with dependency injection in
    FastAPI or similar frameworks.

    Yields:
        Session: A new SQLAlchemy session object.
    """
    with Session(engine) as session:
        yield session
# endregion


# region dependencies
session_dependency = Annotated[Session, Depends(get_session)]
# endregion
