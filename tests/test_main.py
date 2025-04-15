from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

token: str = ""


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


def test_obtain_token():
    """Test the token endpoint with valid credentials of the admin user that is
    created by default.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&scope=&client_id=&client_secret='
    """
    response = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert len(response.json()["access_token"]) == 156
    assert response.json()["token_type"] == "bearer"


def test_obtain_token_invalid_user():
    """Test the token endpoint with invalid credentials.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=invalid_user&password=invalid_password&scope=&client_id=&client_secret='
    """
    response = client.post("/token", data={
        "grant_type": "password",
        "username": "invalid_user",
        "password": "invalid_password",
        "scope": "",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}
