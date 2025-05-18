from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.database import User
from app.models.Role import Role
from app.security.security import get_password_hash


def test_add_staff(session: Session, client: TestClient, faker: Faker):
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
            "password": faker.password(length=10, special_chars=True, digits=True, upper_case=True, lower_case=True)
        }
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert json_response["email"] == "Patricio@udla.edu.ec"
    assert json_response["first_name"] == "Patricio"
    assert json_response["last_name"] == "Estrella"
    assert json_response["role"] == "staff"


def test_add_repeated_staff_email(session: Session, client: TestClient, faker: Faker):
    """Test the staff add endpoint with valid token.

    The curl command to test this endpoint is:
    curl -X 'POST' \\
  'http://127.0.0.1:8000/staff/add' \\
  -H 'accept: application/json' \\
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB1ZGxhLmVkdS5lYyIsInNjb3BlcyI6WyJvcmdhbml6ZXIiXSwiZXhwIjoxNzQ1Mjg1OTM5fQ.l8XXCfcEBdFCYb2yGCLjR8f8bicXDY2dmoNzXdwD0B0' \\
  -H 'Content-Type: application/x-www-form-urlencoded' \\
  -d 'email=Patricio%40udla.edu.ec&first_name=12345678&last_name=Estrella&password=Dinero555%40'
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

    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response1 = client.post(
        "/staff/add",
        headers=headers,
        data={
            "email": "Patricio@udla.edu.ec",
            "first_name": "Patricio",
            "last_name": "Estrella",
            "password": faker.password(length=10, special_chars=True, digits=True, upper_case=True, lower_case=True)
        }
    )

    json_response = response1.json()

    assert response1.status_code == status.HTTP_201_CREATED
    assert json_response["email"] == "Patricio@udla.edu.ec"
    assert json_response["first_name"] == "Patricio"
    assert json_response["last_name"] == "Estrella"
    assert json_response["role"] == "staff"

    response2 = client.post(
        "/staff/add",
        headers=headers,
        data={
            "email": "Patricio@udla.edu.ec",
            "first_name": "Team",
            "last_name": "Rocket",
            "password": faker.password(length=10, special_chars=True, digits=True, upper_case=True, lower_case=True)
        }
    )

    json_response = response2.json()

    assert response2.status_code == status.HTTP_409_CONFLICT
    assert json_response["detail"] == "User with this email already exists"


def test_add_staff_wrong_password(session: Session, client: TestClient):
    """Test the staff add endpoint with valid token.

    The curl command to test this endpoint is:
    curl -X 'POST' \\
  'http://127.0.0.1:8000/staff/add' \\
  -H 'accept: application/json' \\
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB1ZGxhLmVkdS5lYyIsInNjb3BlcyI6WyJvcmdhbml6ZXIiXSwiZXhwIjoxNzQ1MTgwNzYwfQ.SqmQmCb9LwVHbnbzdMU-Pt-dkyKJFezlaxBVIygNyDo' \
  -H 'Content-Type: application/x-www-form-urlencoded' \\
  -d 'email=Patricio%40udla.edu.ec&first_name=Patricio&last_name=Estrella&password=6666666'
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
            "password": "6666666"
        }
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert json_response["detail"][0]["loc"] == ["body", "password"]
    assert json_response["detail"][0]["msg"] == "Value error, Password must have at least 9 characters, 1 lowercase letters, 1 uppercase letters, 1 digit, and 1 special character."


def test_add_staff_wrong_email(session: Session, client: TestClient):
    """Test the staff add endpoint with valid token.

    The curl command to test this endpoint is:
    curl -X 'POST' \\
  'http://127.0.0.1:8000/staff/add' \\
  -H 'accept: application/json' \\
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB1ZGxhLmVkdS5lYyIsInNjb3BlcyI6WyJvcmdhbml6ZXIiXSwiZXhwIjoxNzQ1Mjg1OTM5fQ.l8XXCfcEBdFCYb2yGCLjR8f8bicXDY2dmoNzXdwD0B0' \\
  -H 'Content-Type: application/x-www-form-urlencoded' \\
  -d 'email=Patriciodelocos&first_name=Patricio&last_name=Estrella&password=Dinero555%40'
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
            "email": "Patriciodelocos",
            "first_name": "Patricio",
            "last_name": "Estrella",
            "password": "Dinero555@"
        }
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert json_response["detail"][0]["loc"] == ["body", "email"]
    assert json_response["detail"][0]["msg"] == "value is not a valid email address: An email address must have an @-sign."


def test_add_staff_wrong_first_name(session: Session, client: TestClient):
    """Test the staff add endpoint with valid token.

    curl -X 'POST' \\
    'http://127.0.0.1:8000/staff/add' \\
  -H 'accept: application/json' \\
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB1ZGxhLmVkdS5lYyIsInNjb3BlcyI6WyJvcmdhbml6ZXIiXSwiZXhwIjoxNzQ1MzY5MzYzfQ.n7tn03hrkN3MiID9G6W7gCbD8xQxFfx1ARP8pZp6-tU' \\
  -H 'Content-Type: application/x-www-form-urlencoded' \\
  -d 'email=Patricio%40udla.edu.ec&first_name=777777&last_name=Estrella&password=Dinero555%40'
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
            "first_name": "777777",
            "last_name": "Estrella",
            "password": "Dinero555@"
        }
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert json_response["detail"][0]["loc"] == ["body", "first_name"]
    assert json_response["detail"][0]["msg"] == "Value error, Name cannot consist of only numbers."


def test_add_staff_wrong_last_name(session: Session, client: TestClient):
    """Test the staff add endpoint with valid token.

    curl -X 'POST' \\
    'http://127.0.0.1:8000/staff/add' \\
  -H 'accept: application/json' \\
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB1ZGxhLmVkdS5lYyIsInNjb3BlcyI6WyJvcmdhbml6ZXIiXSwiZXhwIjoxNzQ1MzY5MzYzfQ.n7tn03hrkN3MiID9G6W7gCbD8xQxFfx1ARP8pZp6-tU' \\
  -H 'Content-Type: application/x-www-form-urlencoded' \\
  -d 'email=Patricio%40udla.edu.ec&first_name=Patricio&last_name=d8372846%23&password=Dinero555%40'
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
            "last_name": "d8372846#",
            "password": "Dinero555@"
        }
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert json_response["detail"][0]["loc"] == ["body", "last_name"]
    assert json_response["detail"][0]["msg"] == "Value error, Name must begin with a capital letter."
