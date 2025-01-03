"""
This module contains the main application logic, including routing, middleware,
and the application's lifecycle management. It serves as the entrypoint for
the API and orchestrates interactions with other modules.
"""

import time
import uuid
from typing import Any, Callable

import uvicorn
from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from sqlmodel import Session, select

from api.db.engine import engine
from api.db.setup import create_db_and_tables
from api.models.Role import Role
from api.models.Tags import tags_metadata
from api.models.User import User
from api.routers import users
from api.security.security import get_password_hash


# region FastAPI Configuration
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    This function is used to manage the lifespan of the FastAPI application.
    It runs code before the server starts and after the server stops.

    In this case before the server starts do the following:
    - Create the database and tables if they don't exist

    Args:
        app (FastAPI): The FastAPI application instance.
    Yields:
        None: This function yields control back to the FastAPI application.
    """
    # Code to run before the server starts
    create_db_and_tables()

    # Add admin user if it doesn't exist
    with Session(engine) as session:
        if not (
            session.exec(
                select(User).
                where(User.email == "admin@example.com")
            ).first()
        ):
            admin_user = User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin"),
                role=Role.ADMIN,
                image_uuid=uuid.uuid4()
            )
            session.add(admin_user)
            session.commit()

    yield

    # Code to run after the server stops

app = FastAPI(
    title="Proyecto CAPSTONE - Backend",
    summary="This is the backend for the Proyecto CAPSTONE project. \
    It provides the API for the project's frontend.",
    description="TODO",
    version="0.0.1",
    contact={
        "name": "Gabriel Erazo",
        "url": "https://github.com/gfranciscoerazom",
        "email": "gfranciscoerazom@protonmail.com"
    },
    license_info={
        "name": "Apache 2.0",
        "identifier": "MIT",
    },
    openapi_tags=tags_metadata,  # type: ignore

    lifespan=lifespan,
)
# endregion


# region Routers
app.include_router(users.router)
# endregion


@app.get("/")
async def read_main():
    """
    This function is the main entry point for the application. 
    It handles GET requests to the root path ("/") and returns a JSON response 
    with a message "Hello World".

    Returns:
        dict: A dictionary containing the message "Hello World".
    """
    return {"msg": "Hello World"}

# region Middleware


@app.middleware("http")
async def add_process_time_header(
    request: Request,
    call_next: Callable[[Request], Any]
    # call_next: (Request) -> Any
):
    """
    Middleware to add a custom header indicating the processing time of a request.

    Args:
        request (Request): The incoming HTTP request.
        call_next (Callable[[Request], Any]): A function that processes the request
        and returns a response.

    Returns:
        Response: The HTTP response with an added "X-Process-Time" header
        indicating the time taken to process the request.
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
# endregion


# region Entrypoint
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
# endregion
