from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.database import User
from app.models.Role import Role
from app.security.security import get_password_hash


def test_read_main(client: TestClient):
    """Test the root endpoint to check if returns a hello world message.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/' \\
      -H 'accept: application/json'
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"msg": "Hello World"}


def test_obtain_token(session: Session, client: TestClient):
    """Test the token endpoint with valid credentials of the admin user that is
    created by default.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&scope=organizer&client_id=&client_secret='
    """
    session.add(
        User(
            first_name="Admin",
            last_name="User",
            email="admin@udla.edu.ec",
            hashed_password=get_password_hash("admin"),
            role=Role.ORGANIZER,
        )
    )
    session.commit()

    response = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert len(response.json()["access_token"]) > 10
    assert response.json()["token_type"] == "bearer"


def test_obtain_token_invalid_user(session: Session, client: TestClient):
    """Test the token endpoint with invalid credentials.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=invalid_user&password=invalid_password&scope=organizer&client_id=&client_secret='
    """
    session.add(
        User(
            first_name="Admin",
            last_name="User",
            email="admin@udla.edu.ec",
            hashed_password=get_password_hash("admin"),
            role=Role.ORGANIZER,
        )
    )
    session.commit()

    response = client.post("/token", data={
        "grant_type": "password",
        "username": "invalid_user",
        "password": "invalid_password",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Incorrect username or password"}


def test_obtain_token_invalid_password(session: Session, client: TestClient):
    """Test the token endpoint with invalid password.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin@udla.edu.ec&password=invalid_password&scope=organizer&client_id=&client_secret='
    """
    session.add(
        User(
            first_name="Admin",
            last_name="User",
            email="admin@udla.edu.ec",
            hashed_password=get_password_hash("admin"),
            role=Role.ORGANIZER,
        )
    )
    session.commit()

    response = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "invalid_password",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Incorrect username or password"}


def test_obtain_token_invalid_scope(session: Session, client: TestClient):
    """Try to obtain the token with a scope that can not have that type of user.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin@udla.edu.ec&password=invalid_password&scope=staff&client_id=&client_secret='
    """
    session.add(
        User(
            first_name="Admin",
            last_name="User",
            email="admin@udla.edu.ec",
            hashed_password=get_password_hash("admin"),
            role=Role.ORGANIZER,
        )
    )
    session.commit()

    response = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "staff",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not enough permissions"}
