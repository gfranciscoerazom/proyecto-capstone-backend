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


def test_token_endpoint_with_empty_scope(session: Session, client: TestClient):
    """Test the token endpoint with empty scope string.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&scope=&client_id=&client_secret='
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
        "scope": "",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_token_endpoint_with_mixed_valid_invalid_scopes(session: Session, client: TestClient):
    """Test the token endpoint with a mix of valid and invalid scopes.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&scope=organizer invalid_scope&client_id=&client_secret='
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
        "scope": "organizer invalid_scope",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_token_endpoint_with_all_invalid_scopes(session: Session, client: TestClient):
    """Test the token endpoint with only invalid scopes.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&scope=invalid_scope1 invalid_scope2&client_id=&client_secret='
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
        "scope": "invalid_scope1 invalid_scope2",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not enough permissions"}


def test_assistant_user_with_invalid_scope(session: Session, client: TestClient):
    """Test that an assistant user cannot get organizer scope.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=assistant%40udla.edu.ec&password=assistant123&scope=organizer&client_id=&client_secret='
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
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not enough permissions"}


def test_info_endpoint_with_different_user_roles(session: Session, client: TestClient):
    """Test the /info endpoint with different user roles.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/info' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer <staff_token>'
    """
    # Test with staff user
    staff_user = User(
        first_name="Staff",
        last_name="Member",
        email="staff@udla.edu.ec",
        hashed_password=get_password_hash("staff123"),
        role=Role.STAFF,
    )
    session.add(staff_user)
    session.commit()

    # Get token for staff user
    token_response = client.post("/token", data={
        "grant_type": "password",
        "username": "staff@udla.edu.ec",
        "password": "staff123",
        "scope": "staff",
        "client_id": "",
        "client_secret": ""
    })
    token = token_response.json()["access_token"]

    # Access info endpoint with staff token
    response = client.get("/info", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data["email"] == "staff@udla.edu.ec"
    assert user_data["first_name"] == "Staff"
    assert user_data["last_name"] == "Member"
    assert user_data["role"] == "staff"  # Role is returned in lowercase


def test_info_endpoint_with_malformed_authorization_header(client: TestClient):
    """Test the /info endpoint with malformed authorization header.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/info' \\
      -H 'accept: application/json' \\
      -H 'Authorization: InvalidFormat'
    """
    response = client.get("/info", headers={"Authorization": "InvalidFormat"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_info_endpoint_with_bearer_but_no_token(client: TestClient):
    """Test the /info endpoint with 'Bearer' but no actual token.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/info' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer '
    """
    response = client.get("/info", headers={"Authorization": "Bearer "})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_cors_with_different_origins(client: TestClient):
    """Test CORS behavior with different origins.

    The curl command to test this endpoint is:

    curl -X 'OPTIONS' \\
      'http://127.0.0.1:8000/' \\
      -H 'Origin: https://proyecto-capstone-frontend.onrender.com' \\
      -H 'Access-Control-Request-Method: POST' \\
      -I
    """
    # Test with allowed origin
    response = client.options("/", headers={
        "Origin": "https://proyecto-capstone-frontend.onrender.com",
        "Access-Control-Request-Method": "POST"
    })
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    # Test with backend origin
    response = client.options("/", headers={
        "Origin": "https://proyecto-capstone-backend.onrender.com",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]


def test_middleware_process_time_on_different_endpoints(client: TestClient):
    """Test that the process time middleware works on different endpoints.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/docs' \\
      -H 'accept: text/html' \\
      -I
    """
    # Test on docs endpoint
    response = client.get("/docs")
    assert response.status_code == status.HTTP_200_OK
    assert "X-Process-Time" in response.headers
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0

    # Test on OpenAPI endpoint
    response = client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    assert "X-Process-Time" in response.headers
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0


def test_token_response_structure(session: Session, client: TestClient):
    """Test that the token response has the correct structure and values.

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
    token_data = response.json()
    
    # Check required fields
    assert "access_token" in token_data
    assert "token_type" in token_data
    
    # Check values
    assert token_data["token_type"] == "bearer"
    assert isinstance(token_data["access_token"], str)
    assert len(token_data["access_token"]) > 50  # JWT tokens are typically longer
    
    # Check that there are no extra fields
    expected_fields = {"access_token", "token_type"}
    actual_fields = set(token_data.keys())
    assert actual_fields == expected_fields


def test_user_with_multiple_roles_scope_validation(session: Session, client: TestClient):
    """Test scope validation behavior when organizer tries to access multiple scopes.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&scope=organizer staff assistant&client_id=&client_secret='
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
        "scope": "organizer staff assistant",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_root_endpoint_response_content_type(client: TestClient):
    """Test that the root endpoint returns the correct content type.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/' \\
      -H 'accept: application/json' \\
      -I
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "application/json" in response.headers.get("content-type", "")
    assert response.json() == {"msg": "Hello World"}


def test_404_endpoint(client: TestClient):
    """Test that non-existent endpoints return 404.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/nonexistent' \\
      -H 'accept: application/json'
    """
    response = client.get("/nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_token_endpoint_with_post_method_only(client: TestClient):
    """Test that the token endpoint only accepts POST method.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json'
    """
    response = client.get("/token")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_info_endpoint_with_get_method_only(client: TestClient):
    """Test that the info endpoint only accepts GET method.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/info' \\
      -H 'accept: application/json'
    """
    response = client.post("/info")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_root_endpoint_with_different_http_methods(client: TestClient):
    """Test the root endpoint with different HTTP methods.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/' \\
      -H 'accept: application/json'
    """
    # POST should not be allowed
    response = client.post("/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    # PUT should not be allowed
    response = client.put("/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    # DELETE should not be allowed
    response = client.delete("/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_token_endpoint_with_invalid_grant_type(session: Session, client: TestClient):
    """Test the token endpoint with invalid grant_type.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=invalid&username=admin%40udla.edu.ec&password=admin&scope=organizer&client_id=&client_secret='
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
        "grant_type": "invalid",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_large_scope_string(session: Session, client: TestClient):
    """Test the token endpoint with a very large scope string.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&scope=organizer%20assistant%20staff%20extra1%20extra2&client_id=&client_secret='
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

    # Create a large scope string with valid and invalid scopes
    large_scope = "organizer assistant staff " + " ".join([f"invalid_scope_{i}" for i in range(10)])
    
    response = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": large_scope,
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


def test_token_validation_with_expired_token_simulation(session: Session, client: TestClient):
    """Test behavior when token validation might fail (simulated by using invalid token format).

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/info' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer very.short.token'
    """
    response = client.get("/info", headers={"Authorization": "Bearer very.short.token"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_middleware_preserves_response_status_codes(client: TestClient):
    """Test that middleware doesn't interfere with different status codes.

    The curl commands to test these endpoints are:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/' \\
      -H 'accept: application/json' \\
      -I
      
    curl -X 'GET' \\
      'http://127.0.0.1:8000/nonexistent' \\
      -H 'accept: application/json' \\
      -I
    """
    # Test 200 response
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "X-Process-Time" in response.headers

    # Test 404 response
    response = client.get("/nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "X-Process-Time" in response.headers

    # Test 401 response
    response = client.get("/info")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "X-Process-Time" in response.headers
