"""
This module contains the code that is necessary to run when the application starts.
And some endpoints that don't belong to any specific router.

This module contains the following things:

- lifespan: An async context manager that runs code before the server starts and after the server stops.
- app: A FastAPI application instance that contains the API's configuration.
- logfire: A logging configuration that sends logs to LogFire.
- include_router: Where the routers are added to the FastAPI application.
- endpoint: Endpoint that doesn't belong to any specific router.
- middlewares: Middlewares that add custom headers to the HTTP response.
- Entrypoint: The main entrypoint for the application.
"""
from io import StringIO
import pathlib as pl
import time
from typing import Annotated, Any, Callable

import logfire
import requests
import pandas as pd
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.concurrency import asynccontextmanager
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.db.database import (User, authenticate_user, create_db_and_tables,
                             engine)
from app.models.Role import Role
from app.models.Scopes import Scopes
from app.models.Tags import tags_metadata
from app.models.Token import Token
from app.routers import assistant, events, organizer, staff
from app.security.security import create_access_token, get_password_hash
from app.settings.config import settings

# region FastAPI Configuration


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for the FastAPI application.
    This function is used to manage the lifespan of the FastAPI application.
    It runs code before the server starts and after the server stops.

    In this case before the server starts do the following:
    - Create the database and tables if they don't exist

    And after the server stops do the following:
    - Delete the files in the temp_imgs folder with the exception of the .gitkeep file

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
                select(User.email).
                where(User.email == "admin@udla.edu.ec")
            ).first()
        ):
            admin_user = User(
                first_name="Admin",
                last_name="User",
                email="admin@udla.edu.ec",
                hashed_password=get_password_hash("admin"),
                role=Role.ORGANIZER,
            )
            session.add(admin_user)
            session.commit()

            tables_urls = (
                # Organizers
                ("user", "https://api.mockaroo.com/api/e70b53c0?count=29&key=f4035dc0"),
                # Events
                ("event", "https://api.mockaroo.com/api/d4e79e50?count=250&key=f4035dc0"),
                # Events Dates
                ("eventdate", "https://api.mockaroo.com/api/1fafe150?count=1000&key=f4035dc0"),
                # Staff
                ("user", "https://api.mockaroo.com/api/64205490?count=50&key=f4035dc0"),
                # Assistants
                ("user", "https://api.mockaroo.com/api/db4b6610?count=1000&key=f4035dc0"),
                # Assistants extra data
                ("assistant", "https://api.mockaroo.com/api/af230500?count=1000&key=f4035dc0"),
                # Registration
                ("registration", "https://api.mockaroo.com/api/e851c8c0?count=1000&key=f4035dc0"),
            )

            for table, url in tables_urls:
                response = requests.get(url)
                df = pd.read_csv(StringIO(response.text))  # type: ignore
                df.to_sql(table, con=engine, if_exists="append", index=False)

    yield

    # Code to run after the server stops
    temp_imgs_path = pl.Path("./data/temp_imgs").resolve()
    if temp_imgs_path.exists() and temp_imgs_path.is_dir():
        for item in temp_imgs_path.iterdir():
            if item.name == ".gitkeep":
                continue
            else:
                item.unlink()

app = FastAPI(
    title="Proyecto CAPSTONE - Backend",
    summary="This is the backend for the Proyecto CAPSTONE project. \
    It provides the API for the project's frontend.",
    description="""
# Proyecto CAPSTONE - Backend

This is the backend for the Proyecto CAPSTONE project.

It provides the API for the project's frontend.

This project has the objective of making a platform for the Marketing department, specifically for
free events that are hosted by Universidad de las Americas with the objective of obtaining new candidate

## Authors

This project was developed by:
* Doménica Escobar
* Gabriel Erazo

Tutored by:
* Edwin Garcia

## Useful links

* [Documentation in Swagger UI](http://127.0.0.1:8000/docs)
* [Documentation in ReDoc](http://127.0.0.1:8000/redoc)
* [GitHub Repository](https://github.com/gfranciscoerazom/proyecto-capstone-backend)

```
                                                                           #                        
                                      ###############                    ####                       
                                ########################               #####                        
                            ###########            ######            ######                         
                         #########                   #####         ######                           
                      ########                        ####       ######                             
                                                     #####     ######                               
                                                     ####     ######                                
                                                    ####    #####                                   
                                                  #####   ######                                    
                                                ######  ######                                      
                                              ######  ######                                        
                                            ######  ######                                          
           #####                ################  ###### #############                              
        ########             #################   #####   ###############                            
     ##########      ###   ######      #####   #####                #######                         
   ##########     ###### ######      ######  #####       ##############################             
   ### #####    #############      ######  ######    ############  #####       #############        
      ####   ######## #####      ######  ######   #######        #####                    ######    
    #####  #########  ####     ######  ######   #####         ######                                
   #### ####### ###  ####    ######  ######    ####      #########                                  
  ##########   ##### ############   #####     #################           #######                   
  #######             #########    ####        ###########                                          
                         #                                                                          
                                                                                                    
                                                                                                    
                                                                                                    
 _______ __                              __                                           __ __         
|    ___|  |    .--------.--.--.-----.--|  |.-----.    .-----.-----.----.-----.-----.|__|  |_.---.-.
|    ___|  |    |        |  |  |     |  _  ||  _  |    |     |  -__|  __|  -__|__ --||  |   _|  _  |
|_______|__|    |__|__|__|_____|__|__|_____||_____|    |__|__|_____|____|_____|_____||__|____|___._|
                                                                                                    
                    __                                                                              
.-----.-----.-----.|  |_.-----.    .-----.--.--.-----.    .---.-.--------.-----.                    
|  _  |  -__|     ||   _|  -__|    |  _  |  |  |  -__|    |  _  |        |  -__|                    
|___  |_____|__|__||____|_____|    |__   |_____|_____|    |___._|__|__|__|_____|                    
|_____|                               |__|                                                          
 __                                    __                                                           
|  |.-----.    .-----.--.--.-----.    |  |--.---.-.----.-----.                                      
|  ||  _  |    |  _  |  |  |  -__|    |     |  _  |  __|  -__|                                      
|__||_____|    |__   |_____|_____|    |__|__|___._|____|_____|                                      
                  |__|                                                                              
```
""",
    version="0.0.1",
    contact={
        "name": "Gabriel Erazo",
        "url": "https://github.com/gfranciscoerazom",
        "email": "gfranciscoerazom@protonmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "identifier": "MIT",
    },
    openapi_tags=tags_metadata,  # type: ignore

    lifespan=lifespan,
)
# endregion

logfire.configure(
    token=settings.LOGS_TOKEN,
    code_source=logfire.CodeSource(
        repository="https://github.com/gfranciscoerazom/proyecto-capstone-backend",
        revision="develop",
        root_path="."
    ),
)
logfire.instrument_fastapi(app, capture_headers=True)


# region Routers
app.include_router(organizer.router)
app.include_router(staff.router)
app.include_router(assistant.router)
app.include_router(events.router)
# endregion


@app.post(
    "/token",

    summary="Get an access token",
    response_description="Successful Response with the access token",
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Endpoint to obtain an access token.

    This endpoint allows users to obtain an access token by providing their
    username and password. The token can then be used to authenticate subsequent
    requests.

    \f

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the
            username and password.

    Returns:
        Token: An object containing the access token and token type.

    Raises:
        HTTPException: If the username or password is incorrect, an HTTP 401
            Unauthorized error is raised.
    """
    if not (
        user := authenticate_user(
            email=form_data.username,
            password=form_data.password
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    allowed_scopes: set[Scopes] = user.role.get_allowed_scopes()

    if not all(scope in allowed_scopes for scope in form_data.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={
                "WWW-Authenticate": f'Bearer scope="{", ".join(scope.value for scope in allowed_scopes)}"'
            },
        )

    access_token: str = create_access_token(
        data={
            "sub": user.email,
            "scopes": form_data.scopes,
        }
    )

    return Token(access_token=access_token)


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
