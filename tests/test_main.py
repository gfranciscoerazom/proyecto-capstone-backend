from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

token: str = ""


def test_read_main():
    """Test the root endpoint to check if returns a hello world message.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/' \\
      -H 'accept: application/json'
    """
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
      -d 'grant_type=password&username=admin%40udla.edu.ec&password=admin&scope=organizer&client_id=&client_secret='
    """
    response = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert len(response.json()["access_token"]) > 10
    assert response.json()["token_type"] == "bearer"

    global token
    token = response.json()["access_token"]


def test_obtain_token_invalid_user():
    """Test the token endpoint with invalid credentials.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=invalid_user&password=invalid_password&scope=organizer&client_id=&client_secret='
    """
    response = client.post("/token", data={
        "grant_type": "password",
        "username": "invalid_user",
        "password": "invalid_password",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def test_obtain_token_invalid_password():
    """Test the token endpoint with invalid password.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin@udla.edu.ec&password=invalid_password&scope=organizer&client_id=&client_secret='
    """
    response = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "invalid_password",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def test_obtain_token_invalid_scope():
    """Try to obtain the token with a scope that can not have that type of user.

    The curl command to test this endpoint is:

    curl -X 'POST' \\
      'http://127.0.0.1:8000/token' \\
      -H 'accept: application/json' \\
      -H 'Content-Type: application/x-www-form-urlencoded' \\
      -d 'grant_type=password&username=admin@udla.edu.ec&password=invalid_password&scope=staff&client_id=&client_secret='
    """
    response = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "staff",
        "client_id": "",
        "client_secret": ""
    })
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


def test_get_organizer_info():
    """Test the organizer info endpoint with valid token.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/organizer/info' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer {token}'
    """
    response = client.get("/organizer/info", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["email"] == "admin@udla.edu.ec"
    assert json_response["first_name"] == "Admin"
    assert json_response["last_name"] == "User"
    assert json_response["role"] == "organizer"


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
