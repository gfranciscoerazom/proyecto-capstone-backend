
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db.database import User, get_session
from app.main import app
from app.models.Role import Role
from app.security.security import get_password_hash


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_get_organizer_info(session: Session, client: TestClient):
    """Test the organizer info endpoint with valid token.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/organizer/info' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer {token}'
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

    token = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.get("/organizer/info", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["email"] == "admin@udla.edu.ec"
    assert json_response["first_name"] == "Admin"
    assert json_response["last_name"] == "User"
    assert json_response["role"] == "organizer"
