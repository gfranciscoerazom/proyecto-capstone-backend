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


def test_add_staff(session: Session, client: TestClient):
    """Test the staff add endpoint with valid token.

    The curl command to test this endpoint is:
    curl -X 'POST' \\
      'http://127.0.0.1:8000/staff/add' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB1ZGxhLmVkdS5lYyIsInNjb3BlcyI6WyJvcmdhbml6ZXIiXSwiZXhwIjoxNzQ0OTM0OTUwfQ.iEvVW1-lu1SZCmizTcvP-VRaTw8NUw9uuYLlKsYKfJc' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'email=BobEsponja%40udla.edu.ec&first_name=Bob&last_name=Esponja&password=Dinero666%40'
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

    response = client.post(
        "/staff/add",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "email": "Patricio@udla.edu.ec",
            "first_name": "Patricio",
            "last_name": "Estrella",
            "password": "Dinero555@"
        }
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert json_response["email"] == "Patricio@udla.edu.ec"
    assert json_response["first_name"] == "Patricio"
    assert json_response["last_name"] == "Estrella"
    assert json_response["role"] == "staff"


# curl -X 'POST' \
#   'http://127.0.0.1:8000/assistant/add' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: multipart/form-data' \
#   -F 'gender=male' \
#   -F 'date_of_birth=2025-02-17' \
#   -F 'id_number_type=cedula' \
#   -F 'id_number=Gabriel' \
#   -F 'phone=0995600077' \
#   -F 'accepted_terms=true' \
#   -F 'last_name=Erazo' \
#   -F 'first_name=Gabriel' \
#   -F 'image=@Foto carnet.jpg;type=image/jpeg' \
#   -F 'password=Hola123!@#' \
#   -F 'email=gfranciscoerazom@protonmail.com'
# def test_add_assistant():
#     """Docstring for test_add_assistant
#     """
#     data = {
#         "gender": "male",
#         "date_of_birth": "2025-02-17",
#         "id_number_type": "cedula",
#         "id_number": "Gabriel",
#         "phone": "0995600077",
#         "accepted_terms": "true",
#         "last_name": "Erazo",
#         "first_name": "Gabriel",
#         "password": "Hola123!@#",
#         "email": "gfranciscoerazom@protonmail.com"
#     }
#     # Envía la imagen como parte del formulario
#     with open("./tests/imgs/foto_carne.jpg", "rb") as img_file:
#         files = {"image": ("foto_carnet.jpg", img_file, "image/jpeg")}
#         response = client.post("/assistant/add", data=data, files=files)
#     assert response.status_code in (200, 201, 422)
#     if response.status_code in (200, 201):
#         assert response.json().get("email") == "gfranciscoerazom@protonmail.com"
#     # Si la respuesta es 422, es por validación de FastAPI (por falta de imagen)
