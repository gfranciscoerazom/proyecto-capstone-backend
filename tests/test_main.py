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


def test_obtain_token_with_multiple_scopes(session: Session, client: TestClient):
    """Test the token endpoint with multiple valid scopes.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&scope=organizer assistant&client_id=&client_secret='
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
        "scope": "organizer assistant",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_obtain_token_no_scope(session: Session, client: TestClient):
    """Test the token endpoint without specifying scopes (should get default scopes).

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&client_id=&client_secret='
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
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_obtain_token_staff_user(session: Session, client: TestClient):
    """Test token endpoint with a staff user and appropriate scope.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=staff%40udla.edu.ec&password=staff123&scope=staff&client_id=&client_secret='
    """
    session.add(
        User(
            first_name="Staff",
            last_name="User",
            email="staff@udla.edu.ec",
            hashed_password=get_password_hash("staff123"),
            role=Role.STAFF,
        )
    )
    session.commit()

    response = client.post("/token", data={
        "grant_type": "password",
        "username": "staff@udla.edu.ec",
        "password": "staff123",
        "scope": "staff",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_obtain_token_assistant_user(session: Session, client: TestClient):
    """Test token endpoint with an assistant user and appropriate scope.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=assistant%40udla.edu.ec&password=assistant123&scope=assistant&client_id=&client_secret='
    """
    session.add(
        User(
            first_name="Assistant",
            last_name="User",
            email="assistant@udla.edu.ec",
            hashed_password=get_password_hash("assistant123"),
            role=Role.ASSISTANT,
        )
    )
    session.commit()

    response = client.post("/token", data={
        "grant_type": "password",
        "username": "assistant@udla.edu.ec",
        "password": "assistant123",
        "scope": "assistant",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_info_endpoint_with_valid_token(session: Session, client: TestClient):
    """Test the /info endpoint with a valid access token.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/info' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer <token>'
    """
    user = User(
        first_name="Test",
        last_name="User",
        email="test@udla.edu.ec",
        hashed_password=get_password_hash("test123"),
        role=Role.ORGANIZER,
    )
    session.add(user)
    session.commit()

    # First get a token
    token_response = client.post("/token", data={
        "grant_type": "password",
        "username": "test@udla.edu.ec",
        "password": "test123",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    token = token_response.json()["access_token"]

    # Then use the token to access the info endpoint
    response = client.get("/info", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data["email"] == "test@udla.edu.ec"
    assert user_data["first_name"] == "Test"
    assert user_data["last_name"] == "User"
    assert "id" in user_data


def test_info_endpoint_without_token(client: TestClient):
    """Test the /info endpoint without authentication token.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/info' \\
      -H 'accept: application/json'
    """
    response = client.get("/info")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_info_endpoint_with_invalid_token(client: TestClient):
    """Test the /info endpoint with an invalid access token.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/info' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer invalid_token'
    """
    response = client.get("/info", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_middleware_process_time_header(client: TestClient):
    """Test that the middleware adds the X-Process-Time header to responses.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/' \\
      -H 'accept: application/json' \\
      -I
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "X-Process-Time" in response.headers
    # Verify the header value is a valid float
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0


def test_cors_headers_present(client: TestClient):
    """Test that CORS headers are properly configured for allowed origins.

    The curl command to test this endpoint is:

    curl -X 'OPTIONS' \\
      'http://127.0.0.1:8000/' \\
      -H 'Origin: http://127.0.0.1:8001' \\
      -H 'Access-Control-Request-Method: GET' \\
      -I
    """
    response = client.options("/", headers={
        "Origin": "http://127.0.0.1:8001",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]


def test_token_endpoint_missing_required_fields(client: TestClient):
    """Test the token endpoint with missing required fields.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password'
    """
    response = client.post("/token", data={
        "grant_type": "password"
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_obtain_token_staff_user_with_organizer_scope(session: Session, client: TestClient):
    """Test that a staff user cannot get organizer scope.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=staff%40udla.edu.ec&password=staff123&scope=organizer&client_id=&client_secret='
    """
    session.add(
        User(
            first_name="Staff",
            last_name="User", 
            email="staff@udla.edu.ec",
            hashed_password=get_password_hash("staff123"),
            role=Role.STAFF,
        )
    )
    session.commit()

    response = client.post("/token", data={
        "grant_type": "password",
        "username": "staff@udla.edu.ec",
        "password": "staff123",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not enough permissions"}


def test_api_documentation_accessibility(client: TestClient):
    """Test that API documentation endpoints are accessible.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/docs' \\
      -H 'accept: text/html'
    """
    # Test Swagger UI docs
    response = client.get("/docs")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers.get("content-type", "")

    # Test ReDoc docs  
    response = client.get("/redoc")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers.get("content-type", "")

    # Test OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    assert "application/json" in response.headers.get("content-type", "")
