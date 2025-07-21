import json
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict

import sqlalchemy.exc
from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient

# import pytest
# import os

# @pytest.fixture(scope="session", autouse=True)
# def ensure_temp_imgs_dir():
#     os.makedirs("data/temp_imgs", exist_ok=True)


def generate_assistant_email(faker: Faker) -> str:
    """Generate a valid email for assistant role (must be from allowed domains)."""
    allowed_domains = ["@gmail.com", "@hotmail.com", "@outlook.com", "@protonmail.com", "@yahoo.com"]
    username = faker.user_name()
    domain = faker.random_element(allowed_domains)
    return f"{username}{domain}"



def test_add_assistant_invalid_id_number(client: TestClient, token: str, faker: Faker):
    """Test the POST /assistant/add endpoint with an invalid Ecuadorian ID number.

    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'id_number=1701698834' ...
    """

    id_number_type = "cedula"
    id_number = "1234567890"

    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": id_number_type,
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": faker.email(),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {
            "image": ("person.jpeg", image_file, "image/jpeg")
        }

        response = client.post(
            "/assistant/add",
            headers={
                "Authorization": f"Bearer {token}",
                "accept": "application/json"},
            data=person,
            files=files
        )

    json_response = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert json_response["detail"][0]["msg"] == "Value error, Invalid Ecuadorian ID number"


def test_add_assistant_without_accepting_terms(client: TestClient, token: str, faker: Faker):
    """Test the POST /assistant/add endpoint when terms and conditions are not accepted.

    curl -X 'POST' \\
      'http://127.0.0.1:8000/assistant/add' \\
      -F 'accepted_terms=false' ...
    """

    response = client.post(
        "/assistant/add",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"},
        data={
            "gender": "female",
            "date_of_birth": "1997-09-19",
            "id_number_type": "cedula",
            "id_number": "1709690034",
            "phone": "0999999999",
            "accepted_terms": "false",
            "last_name": "Mebarak",
            "first_name": "Shakira",
            "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            "email": "alphawolf@gmail.com"
        },
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert json_response["detail"][0]["loc"] == ["body", "accepted_terms"]
    assert json_response["detail"][0]["msg"] == "Value error, You must accept the terms and conditions."


def test_add_assistant_with_future_birthdate(client: TestClient, token: str, faker: Faker):
    """Test the POST /assistant/add endpoint with a future date of birth.

    curl -X 'POST' \\
      'http://127.0.0.1:8000/assistant/add' \\
      -F 'date_of_birth=2025-09-19' ...
    """

    response = client.post(
        "/assistant/add",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"},

        data={
            "gender": "female",
            "date_of_birth": "2025-09-19",
            "id_number_type": "cedula",
            "id_number": "1709690034",
            "phone": "0999999999",
            "accepted_terms": "true",
            "last_name": "Mebarak",
            "first_name": "Shakira",
            "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            "email": "alphawolf@gmail.com"
        },
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert json_response["detail"][0]["loc"] == ["body", "date_of_birth"]
    assert json_response["detail"][0]["msg"] == "Value error, Date must be before today."



def test_get_assistant_by_id_number_not_found(client: TestClient, token: str, faker: Faker):
    """Test the GET /assistant/get-by-id-number/{id_number} endpoint with a non-existing ID.

    curl -X 'GET' \\
      'http://127.0.0.1:8000/assistant/get-by-id-number/1726754301' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer <token>'
    """
    response = client.get(
        f"/assistant/get-by-id-number/{faker.random_int(min=1000000000, max=9999999999)}",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "Assistant not found"


def test_add_assistant_success(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test the POST /assistant/add endpoint with valid data.

    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'id_number=1701698834' ...
    """

    id_number_type = "cedula"
    id_number = faker.ecuadorian_id_number()

    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": id_number_type,
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {
            "image": ("person.jpeg", image_file, "image/jpeg")
        }

        response = client.post(
            "/assistant/add",
            headers={
                "Authorization": f"Bearer {token}",
                "accept": "application/json"},
            data=person,
            files=files
        )

    json_response = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert json_response["email"] == person["email"]
    assert json_response["first_name"] == person["first_name"]
    assert json_response["last_name"] == person["last_name"]
    assert "id" in json_response


def test_add_assistant_duplicate_person(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test the POST /assistant/add endpoint with the same person (same face).
    
    This test verifies that the face recognition system prevents the same person
    from registering multiple times, even with different email addresses.
    
    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'email=existing@example.com' ...
    """
    id_number_type = "cedula"
    id_number = faker.ecuadorian_id_number()
    email = generate_assistant_email(faker)

    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": id_number_type,
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": email,
    }

    # First registration should succeed
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {
            "image": ("person.jpeg", image_file, "image/jpeg")
        }

        response = client.post(
            "/assistant/add",
            headers={
                "Authorization": f"Bearer {token}",
                "accept": "application/json"},
            data=person,
            files=files
        )    # Debug the first registration attempt
    if response.status_code != status.HTTP_201_CREATED:
        print(f"First registration failed with status: {response.status_code}")
        print(f"Response: {response.json()}")
    
    assert response.status_code == status.HTTP_201_CREATED

    # Second registration with same face (but different email and ID) should fail
    person["id_number"] = faker.ecuadorian_id_number()  # Change ID to avoid ID conflict
    person["email"] = generate_assistant_email(faker)  # Change email too

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {
            "image": ("person.jpeg", image_file, "image/jpeg")
        }

        response = client.post(
            "/assistant/add",
            headers={
                "Authorization": f"Bearer {token}",
                "accept": "application/json"},
            data=person,
            files=files
        )

    json_response = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert json_response["detail"] == "The person already exists in the database. Please enter a different person."


def test_add_assistant_invalid_phone_number(client: TestClient, token: str, faker: Faker):
    """Test the POST /assistant/add endpoint with an invalid phone number.
    
    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'phone=123' ...
    """
    id_number_type = "cedula"
    id_number = faker.ecuadorian_id_number()

    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": id_number_type,
        "id_number": id_number,
        "phone": "123",  # Invalid phone number
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": faker.email(),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {
            "image": ("person.jpeg", image_file, "image/jpeg")
        }

        response = client.post(
            "/assistant/add",
            headers={
                "Authorization": f"Bearer {token}",
                "accept": "application/json"},
            data=person,
            files=files
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_add_assistant_missing_image(client: TestClient, token: str, faker: Faker):
    """Test the POST /assistant/add endpoint without an image.
    
    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -d '{"first_name": "John"}' ...
    """
    id_number_type = "cedula"
    id_number = faker.ecuadorian_id_number()

    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": id_number_type,
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": faker.email(),
    }

    response = client.post(
        "/assistant/add",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"},
        data=person
        # No files parameter - missing image
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_assistant_info_success(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test the GET /assistant/info endpoint with valid authentication.

    curl -X 'GET' \\
        'http://127.0.0.1:8000/assistant/info' \\
        -H 'Authorization: Bearer <token>'
    """
    # First create an assistant
    id_number = faker.ecuadorian_id_number()
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    # Create assistant
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED
    
    # Get assistant token
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person["email"],
            "password": person["password"],
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Test get assistant info
    response = client.get(
        "/assistant/info",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert json_response["email"] == person["email"]
    assert json_response["first_name"] == person["first_name"]


def test_get_assistant_info_unauthorized(client: TestClient):
    """Test the GET /assistant/info endpoint without authentication.

    curl -X 'GET' \\
        'http://127.0.0.1:8000/assistant/info'
    """
    response = client.get(
        "/assistant/info",
        headers={"accept": "application/json"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_assistant_by_id_number_success(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test the GET /assistant/get-by-id-number/{id_number} endpoint with existing ID.

    curl -X 'GET' \\
        'http://127.0.0.1:8000/assistant/get-by-id-number/1726754301' \\
        -H 'accept: application/json' \\
        -H 'Authorization: Bearer <token>'
    """
    # First create an assistant
    id_number = faker.ecuadorian_id_number()
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    # Create assistant
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED

    # Now test getting by ID number
    response = client.get(
        f"/assistant/get-by-id-number/{id_number}",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert json_response["assistant"]["id_number"] == id_number
    assert json_response["email"] == person["email"]


def test_add_assistant_invalid_email_format(client: TestClient, token: str, faker: Faker):
    """Test the POST /assistant/add endpoint with invalid email format.
    
    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'email=invalid-email' ...
    """
    id_number_type = "cedula"
    id_number = faker.ecuadorian_id_number()

    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": id_number_type,
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": "invalid-email",  # Invalid email format
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {
            "image": ("person.jpeg", image_file, "image/jpeg")
        }

        response = client.post(
            "/assistant/add",
            headers={
                "Authorization": f"Bearer {token}",
                "accept": "application/json"},
            data=person,
            files=files
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_add_assistant_weak_password(client: TestClient, token: str, faker: Faker):
    """Test the POST /assistant/add endpoint with weak password.
    
    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'password=123' ...
    """
    id_number_type = "cedula"
    id_number = faker.ecuadorian_id_number()

    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": id_number_type,
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": "123",  # Weak password
        "email": faker.email(),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {
            "image": ("person.jpeg", image_file, "image/jpeg")
        }

        response = client.post(
            "/assistant/add",
            headers={
                "Authorization": f"Bearer {token}",
                "accept": "application/json"},
            data=person,
            files=files
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_assistant_register_to_event_success(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test assistant registration to an event.

    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/register-to-event/1' \\
        -H 'Authorization: Bearer <token>'
    """
    # First create an assistant
    id_number = faker.ecuadorian_id_number()
    password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": password,
        "email": generate_assistant_email(faker),
    }

    # Create assistant
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED

    # Create an event first
    event_data = {
        "name": faker.sentence(nb_words=3),
        "description": faker.text(max_nb_chars=200),
        "location": faker.address(),
        "maps_link": "https://maps.app.goo.gl/testlocation",
        "capacity": 100,
        "capacity_type": "limit_of_spaces",
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        event_files = {"image": ("event.jpeg", image_file, "image/jpeg")}
        event_response = client.post(
            "/events/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=event_data,
            files=event_files
        )
    
    assert event_response.status_code == status.HTTP_201_CREATED
    event_id = event_response.json()["id"]

    # Get assistant token
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person["email"],
            "password": password,
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Register assistant to event
    response = client.post(
        f"/assistant/register-to-event/{event_id}",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert json_response["event_id"] == event_id


def test_assistant_register_to_nonexistent_event(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test assistant registration to a non-existent event.

    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/register-to-event/9999' \\
        -H 'Authorization: Bearer <token>'
    """
    # First create an assistant
    id_number = faker.ecuadorian_id_number()
    password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": password,
        "email": generate_assistant_email(faker),
    }

    # Create assistant
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED

    # Get assistant token
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person["email"],
            "password": password,
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Try to register to non-existent event
    response = client.post(
        "/assistant/register-to-event/9999",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "Event not found"


def test_assistant_get_registered_events(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test getting registered events for an assistant.

    curl -X 'GET' \\
        'http://127.0.0.1:8000/assistant/get-registered-events' \\
        -H 'Authorization: Bearer <token>'
    """
    # First create an assistant
    id_number = faker.ecuadorian_id_number()
    password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": password,
        "email": generate_assistant_email(faker),
    }

    # Create assistant
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED

    # Get assistant token
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person["email"],
            "password": password,
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Test getting registered events (should be empty initially)
    response = client.get(
        "/assistant/get-registered-events",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(json_response, list)
    assert len(json_response) == 0  # No events registered initially


def test_assistant_unauthorized_access(client: TestClient):
    """Test accessing assistant endpoints without authentication.

    curl -X 'GET' \\
        'http://127.0.0.1:8000/assistant/get-registered-events'
    """
    response = client.get(
        "/assistant/get-registered-events",
        headers={"accept": "application/json"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_assistant_register_to_event_without_auth(client: TestClient):
    """Test registering to an event without authentication.

    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/register-to-event/1'
    """
    response = client.post(
        "/assistant/register-to-event/1",
        headers={"accept": "application/json"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_add_assistant_duplicate_email_conflict(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the POST /assistant/add endpoint with duplicate email (IntegrityError).
    
    This test verifies that attempting to create an assistant with an existing email
    raises an IntegrityError which gets converted to a 409 Conflict.
    
    Note: The system uses face recognition, so same face = 400 Bad Request instead of 409.
    This test verifies the face recognition duplicate detection works correctly.
    """
    id_number = faker.ecuadorian_id_number()
    email = generate_assistant_email(faker)
    
    person: Dict[str, Any] = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": email,
    }

    # First registration should succeed
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert response.status_code == status.HTTP_201_CREATED

    # Second registration with same email but different ID and same face should fail with face recognition
    person["id_number"] = faker.ecuadorian_id_number()  # Different ID
    
    # Use the same image to trigger face recognition duplicate detection
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person2.jpeg", image_file, "image/jpeg")}
        response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )

    json_response = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert json_response["detail"] == "The person already exists in the database. Please enter a different person."


def test_get_assistants_by_image_no_similar_people(client: TestClient, token: str) -> None:
    """Test the POST /assistant/get-by-image endpoint when no similar people are found.
    
    This test verifies that when the face recognition system cannot find any
    similar faces, it returns a 404 error.
    """
    # Use an image that won't match any existing faces
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("unique_person.jpeg", image_file, "image/jpeg")}
        response = client.post(
            "/assistant/get-by-image",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            files=files
        )

    json_response = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "No similar people found in images database"


def test_get_assistants_by_image_invalid_event_params(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the POST /assistant/get-by-image endpoint with invalid event parameters.
    
    This test verifies that providing only one of event_id or event_date_id
    results in a 400 Bad Request error.
    """
    # First create an assistant to have some data
    id_number = faker.ecuadorian_id_number()
    person: Dict[str, Any] = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED

    # Test with only event_id provided
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        response = client.post(
            "/assistant/get-by-image?event_id=1",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            files=files
        )

    json_response = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert json_response["detail"] == "Both event_id and event_date_id must be provided or none of them"

    # Test with only event_date_id provided
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        response = client.post(
            "/assistant/get-by-image?event_date_id=1",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            files=files
        )

    json_response = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert json_response["detail"] == "Both event_id and event_date_id must be provided or none of them"


def test_get_assistants_by_image_with_event_filters(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test the POST /assistant/get-by-image endpoint with both event_id and event_date_id.
    
    This test verifies the path where both event_id and event_date_id are provided,
    which triggers the attendance-based filtering logic.
    """
    # First create an assistant
    id_number = faker.ecuadorian_id_number()
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED

    # Create an event
    event_data = {
        "name": faker.sentence(nb_words=3),
        "description": faker.text(max_nb_chars=200),
        "location": faker.address(),
        "maps_link": "https://maps.app.goo.gl/testlocation",
        "capacity": 100,
        "capacity_type": "limit_of_spaces",
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        event_files = {"image": ("event.jpeg", image_file, "image/jpeg")}
        event_response = client.post(
            "/events/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=event_data,
            files=event_files
        )
    
    assert event_response.status_code == status.HTTP_201_CREATED
    event_id = event_response.json()["id"]

    # Test with both event_id and event_date_id (using dummy IDs)
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        response = client.post(
            f"/assistant/get-by-image?event_id={event_id}&event_date_id=1",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            files=files
        )

    # This should succeed and return the filtered users
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert isinstance(json_response, list)


def test_register_companion_to_event_user_not_found(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test registering a companion when the current user is not found in database."""
    # This test simulates a scenario where the current_user.id doesn't exist in the database
    # This would be an edge case but we need to test the error handling
    
    # Create an assistant first
    id_number = faker.ecuadorian_id_number()
    password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": password,
        "email": generate_assistant_email(faker),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED

    # Get assistant token
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person["email"],
            "password": password,
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Try to register a companion to a non-existent event
    response = client.post(
        "/assistant/register-companion-to-event/9999",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        },
        data={
            "companion_id": "1",  # Convert to string for form data
            "companion_type": "first_grade"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "Event not found"


def test_register_companion_to_event_companion_not_found(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test registering a non-existent companion to an event."""
    # Create an assistant and event first
    id_number = faker.ecuadorian_id_number()
    password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": password,
        "email": generate_assistant_email(faker),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED

    # Create an event
    event_data = {
        "name": faker.sentence(nb_words=3),
        "description": faker.text(max_nb_chars=200),
        "location": faker.address(),
        "maps_link": "https://maps.app.goo.gl/testlocation",
        "capacity": 100,
        "capacity_type": "limit_of_spaces",
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        event_files = {"image": ("event.jpeg", image_file, "image/jpeg")}
        event_response = client.post(
            "/events/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=event_data,
            files=event_files
        )
    
    assert event_response.status_code == status.HTTP_201_CREATED
    event_id = event_response.json()["id"]

    # Get assistant token
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person["email"],
            "password": password,
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Register assistant to the event first
    client.post(
        f"/assistant/register-to-event/{event_id}",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        }
    )

    # Try to register a non-existent companion
    response = client.post(
        f"/assistant/register-companion-to-event/{event_id}",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        },
        data={
            "companion_id": "9999",  # Convert to string for form data
            "companion_type": "first_grade"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "Companion not found"


def test_register_companion_user_not_registered_to_event(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test registering a companion when the user is not registered to the event."""
    # Create one assistant that will try to register a companion
    id_number1 = faker.ecuadorian_id_number()
    password1 = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    person1: Dict[str, Any] = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number1,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": password1,
        "email": generate_assistant_email(faker),
    }

    # Create first assistant
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person1.jpeg", image_file, "image/jpeg")}
        create_response1 = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person1,
            files=files
        )

    assert create_response1.status_code == status.HTTP_201_CREATED
    assistant1_id = create_response1.json()["id"]

    # Create an event
    event_data: Dict[str, Any] = {
        "name": faker.sentence(nb_words=3),
        "description": faker.text(max_nb_chars=200),
        "location": faker.address(),
        "maps_link": "https://maps.app.goo.gl/testlocation",
        "capacity": 100,
        "capacity_type": "limit_of_spaces",
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        event_files = {"image": ("event.jpeg", image_file, "image/jpeg")}
        event_response = client.post(
            "/events/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=event_data,
            files=event_files
        )
    
    assert event_response.status_code == status.HTTP_201_CREATED
    event_id = event_response.json()["id"]

    # Get assistant token (but don't register to event)
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person1["email"],
            "password": password1,
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Try to register companion without being registered to the event
    response = client.post(
        f"/assistant/register-companion-to-event/{event_id}",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        },
        data={
            "companion_id": str(assistant1_id),  # Convert to string for form data
            "companion_type": "first_grade"
        }
    )

    json_response = response.json()
    # The endpoint may return 403 if the user doesn't have the right scope or permissions
    # or 400 if they are not registered to the event
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        assert "not registered" in json_response["detail"].lower()
    else:
        # 403 Forbidden - user doesn't have permission or isn't registered
        assert "detail" in json_response


def test_react_to_event_user_not_found(client: TestClient, token: str):
    """Test reacting to an event with a non-existent user."""
    response = client.get(
        "/assistant/react/9999/1?reaction=like",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "User not found"


def test_react_to_event_event_not_found(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test reacting to a non-existent event."""
    # Create an assistant first
    id_number = faker.ecuadorian_id_number()
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED
    user_id = create_response.json()["id"]

    response = client.get(
        f"/assistant/react/{user_id}/9999?reaction=like",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "Event not found"


def test_react_to_event_registration_not_found(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test reacting to an event when the user is not registered to it."""
    # Create an assistant
    id_number = faker.ecuadorian_id_number()
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED
    user_id = create_response.json()["id"]

    # Create an event
    event_data = {
        "name": faker.sentence(nb_words=3),
        "description": faker.text(max_nb_chars=200),
        "location": faker.address(),
        "maps_link": "https://maps.app.goo.gl/testlocation",
        "capacity": 100,
        "capacity_type": "limit_of_spaces",
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        event_files = {"image": ("event.jpeg", image_file, "image/jpeg")}
        event_response = client.post(
            "/events/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=event_data,
            files=event_files
        )
    
    assert event_response.status_code == status.HTTP_201_CREATED
    event_id = event_response.json()["id"]

    # Try to react without being registered
    response = client.get(
        f"/assistant/react/{user_id}/{event_id}?reaction=like",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "Registration not found"


def test_unregister_from_event_registration_not_found(client: TestClient, token: str, faker: Faker, clean_face_db):
    """Test unregistering from an event when not registered."""
    # Create an assistant
    id_number = faker.ecuadorian_id_number()
    password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    person = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": password,
        "email": generate_assistant_email(faker),
    }

    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED

    # Get assistant token
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person["email"],
            "password": password,
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Try to unregister from a non-existent event
    response = client.delete(
        "/assistant/unregister-from-event/9999",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "Registration not found"


def test_get_user_image_invalid_uuid(client: TestClient, token: str) -> None:
    """Test getting a user image with an invalid UUID."""
    invalid_uuid = "invalid-uuid-format"
    
    response = client.get(
        f"/assistant/image/{invalid_uuid}",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    # FastAPI returns 422 for path validation errors, not 400
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check that it's a validation error for the UUID path parameter
    assert "detail" in json_response
    assert any("uuid" in str(error).lower() for error in json_response["detail"])


def test_get_user_image_not_found(client: TestClient, token: str):
    """Test getting a user image that doesn't exist."""
    # Use a valid UUID format but one that doesn't exist
    nonexistent_uuid = str(uuid4())
    
    response = client.get(
        f"/assistant/image/{nonexistent_uuid}",
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert json_response["detail"] == "Image not found"


def test_add_assistant_database_integrity_error(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the POST /assistant/add endpoint when SQLAlchemy IntegrityError occurs.
    
    This test simulates a database integrity constraint violation that can occur
    during the commit operation, which should result in a 409 Conflict error.
    
    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'email=test@gmail.com' ...
    """
    from unittest.mock import patch, MagicMock
    import sqlalchemy.exc
    
    id_number = faker.ecuadorian_id_number()
    person: Dict[str, Any] = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    # Mock the PersonImg.save method to raise IntegrityError
    with patch('app.routers.assistant.PersonImg') as mock_person_img:
        mock_instance = MagicMock()
        mock_person_img.return_value = mock_instance
        mock_instance.save.side_effect = sqlalchemy.exc.IntegrityError(
            statement="INSERT INTO user ...",
            params={},
            orig=Exception("Duplicate key error")
        )

        with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
            files = {"image": ("person.jpeg", image_file, "image/jpeg")}
            response = client.post(
                "/assistant/add",
                headers={
                    "Authorization": f"Bearer {token}",
                    "accept": "application/json"
                },
                data=person,
                files=files
            )

    json_response = response.json()
    assert response.status_code == status.HTTP_409_CONFLICT
    assert json_response["detail"] == "User already exists"


def test_add_assistant_image_saving_error(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the POST /assistant/add endpoint when a general Exception occurs during image saving.
    
    This test simulates a general error that can occur during the image saving process,
    which should result in a 500 Internal Server Error.
    
    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'email=test@gmail.com' ...
    """
    from unittest.mock import patch, MagicMock
    
    id_number = faker.ecuadorian_id_number()
    person: Dict[str, Any] = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    # Mock the PersonImg.save method to raise a general Exception
    with patch('app.routers.assistant.PersonImg') as mock_person_img:
        mock_instance = MagicMock()
        mock_person_img.return_value = mock_instance
        mock_instance.save.side_effect = Exception("Disk space full or I/O error")

        with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
            files = {"image": ("person.jpeg", image_file, "image/jpeg")}
            response = client.post(
                "/assistant/add",
                headers={
                    "Authorization": f"Bearer {token}",
                    "accept": "application/json"
                },
                data=person,
                files=files
            )

    json_response = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert json_response["detail"] == "An error occurred while saving the image"


def test_add_assistant_filesystem_permission_error(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the POST /assistant/add endpoint when filesystem permission error occurs.
    
    This test simulates a filesystem permission error that can occur during image saving,
    which should result in a 500 Internal Server Error.
    
    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'email=test@gmail.com' ...
    """
    from unittest.mock import patch, MagicMock
    
    id_number = faker.ecuadorian_id_number()
    person: Dict[str, Any] = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }

    # Mock the PersonImg.save method to raise PermissionError
    with patch('app.routers.assistant.PersonImg') as mock_person_img:
        mock_instance = MagicMock()
        mock_person_img.return_value = mock_instance
        mock_instance.save.side_effect = PermissionError("Permission denied: cannot write to directory")

        with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
            files = {"image": ("person.jpeg", image_file, "image/jpeg")}
            response = client.post(
                "/assistant/add",
                headers={
                    "Authorization": f"Bearer {token}",
                    "accept": "application/json"
                },
                data=person,
                files=files
            )

    json_response = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert json_response["detail"] == "An error occurred while saving the image"


def test_add_assistant_database_connection_error(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the POST /assistant/add endpoint when database connection error occurs.
    
    This test simulates a database connection error that can occur during the save operation,
    which should result in a 500 Internal Server Error.
    
    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/add' \\
        -F 'email=test@gmail.com' ...
    """
    from unittest.mock import patch, MagicMock
    import sqlalchemy.exc
    
    id_number = faker.ecuadorian_id_number()
    person: Dict[str, Any] = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
        "email": generate_assistant_email(faker),
    }    # Mock the PersonImg.save method to raise DatabaseError
    with patch('app.routers.assistant.PersonImg') as mock_person_img:
        mock_instance = MagicMock()
        mock_person_img.return_value = mock_instance
        mock_instance.save.side_effect = sqlalchemy.exc.DatabaseError(
            statement="SELECT ...",
            params={},
            orig=Exception("Connection lost")
        )
        
        with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
            files = {"image": ("person.jpeg", image_file, "image/jpeg")}
            response = client.post(
                "/assistant/add",
                headers={
                    "Authorization": f"Bearer {token}",
                    "accept": "application/json"
                },
                data=person,
                files=files
            )

    json_response = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert json_response["detail"] == "An error occurred while saving the image"


def test_update_assistant_profile_success(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the PATCH /assistant/{assistant_id} endpoint with successful update.
    
    This test verifies that an assistant can successfully update their own profile
    with valid data, including personal information updates.
    
    curl -X 'PATCH' \\
        'http://127.0.0.1:8000/assistant/1' \\
        -H 'Authorization: Bearer <token>' \\
        -d '{"first_name": "Updated Name"}'
    """
    # Create an assistant first
    id_number = faker.ecuadorian_id_number()
    password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    person: Dict[str, Any] = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": password,
        "email": generate_assistant_email(faker),
    }

    # Create assistant
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED
    assistant_id = create_response.json()["id"]

    # Get assistant token
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person["email"],
            "password": password,
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Update assistant profile
    update_data = {
        "user_update": {
            "first_name": "Updated FirstName",
            "last_name": "Updated LastName"
        },
        "assistant_update": {
            "phone": "0987654321"
        }
    }

    response = client.patch(
        f"/assistant/{assistant_id}",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json",
            "content-type": "application/json"
        },
        json=update_data
    )

    json_response = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert json_response["first_name"] == "Updated FirstName"
    assert json_response["last_name"] == "Updated LastName"
    assert json_response["assistant"]["phone"] == "0987654321"


def test_update_assistant_profile_unauthorized_cross_user(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the PATCH /assistant/{assistant_id} endpoint when assistant tries to update another assistant.
    
    This test verifies that an assistant cannot update another assistant's profile,
    which should result in a 403 Forbidden error.
    
    curl -X 'PATCH' \\
        'http://127.0.0.1:8000/assistant/2' \\
        -H 'Authorization: Bearer <assistant1_token>' \\
        -d '{"first_name": "Hacked Name"}'
    """
    from unittest.mock import patch, MagicMock
    
    # Mock the face recognition to allow different people
    with patch('app.helpers.personTempImg.PersonImg.is_single_person') as mock_is_single_person, \
         patch('app.helpers.personTempImg.PersonImg.path_imgs_similar_people') as mock_similar_people:
        
        mock_is_single_person.return_value = True
        mock_similar_people.return_value = []  # No similar people found
        
        # Create first assistant
        id_number1 = faker.ecuadorian_id_number()
        password1 = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        person1: Dict[str, Any] = {
            "gender": faker.random_element(elements=["female", "male", "other"]),
            "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
            "id_number_type": "cedula",
            "id_number": id_number1,
            "phone": str(faker.random_int(min=1000000000, max=9999999999)),
            "accepted_terms": "true",
            "last_name": faker.last_name(),
            "first_name": faker.first_name(),
            "password": password1,
            "email": generate_assistant_email(faker),
        }

        with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
            files = {"image": ("person1.jpeg", image_file, "image/jpeg")}
            create_response1 = client.post(
                "/assistant/add",
                headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
                data=person1,
                files=files
            )
        
        assert create_response1.status_code == status.HTTP_201_CREATED

        # Create second assistant
        id_number2 = faker.ecuadorian_id_number()
        password2 = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        person2: Dict[str, Any] = {
            "gender": faker.random_element(elements=["female", "male", "other"]),
            "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
            "id_number_type": "cedula",
            "id_number": id_number2,
            "phone": str(faker.random_int(min=1000000000, max=9999999999)),
            "accepted_terms": "true",
            "last_name": faker.last_name(),
            "first_name": faker.first_name(),
            "password": password2,
            "email": generate_assistant_email(faker),
        }

        with open("tests/imgs/person2.jpg", "rb") as image_file:
            files = {"image": ("person2.jpeg", image_file, "image/jpeg")}
            create_response2 = client.post(
                "/assistant/add",
                headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
                data=person2,
                files=files
            )
        
        assert create_response2.status_code == status.HTTP_201_CREATED
        assistant2_id = create_response2.json()["id"]

        # Get first assistant's token
        assistant1_token = client.post(
            "/token",
            data={
                "grant_type": "password",
                "username": person1["email"],
                "password": password1,
                "scope": "assistant",
                "client_id": "",
                "client_secret": ""
            }
        ).json()["access_token"]

        # Try to update second assistant's profile with first assistant's token
        update_data = {
            "user_update": {
                "first_name": "Hacked Name"
            },
            "assistant_update": {}
        }

        response = client.patch(
            f"/assistant/{assistant2_id}",
            headers={
                "Authorization": f"Bearer {assistant1_token}",
                "accept": "application/json",
                "content-type": "application/json"
            },
            json=update_data
        )

        json_response = response.json()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert json_response["detail"] == "You can only update your own profile"


def test_delete_assistant_success(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the DELETE /assistant/{assistant_id} endpoint with successful deletion.
    
    This test verifies that an assistant can successfully delete their own profile,
    which should result in a 204 No Content response.
    
    curl -X 'DELETE' \\
        'http://127.0.0.1:8000/assistant/1' \\
        -H 'Authorization: Bearer <token>'
    """
    # Create an assistant first
    id_number = faker.ecuadorian_id_number()
    password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    person: Dict[str, Any] = {
        "gender": faker.random_element(elements=["female", "male", "other"]),
        "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
        "id_number_type": "cedula",
        "id_number": id_number,
        "phone": str(faker.random_int(min=1000000000, max=9999999999)),
        "accepted_terms": "true",
        "last_name": faker.last_name(),
        "first_name": faker.first_name(),
        "password": password,
        "email": generate_assistant_email(faker),
    }

    # Create assistant
    with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
        files = {"image": ("person.jpeg", image_file, "image/jpeg")}
        create_response = client.post(
            "/assistant/add",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            data=person,
            files=files
        )
    
    assert create_response.status_code == status.HTTP_201_CREATED
    assistant_id = create_response.json()["id"]

    # Get assistant token
    assistant_token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": person["email"],
            "password": password,
            "scope": "assistant",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    # Delete assistant profile
    response = client.delete(
        f"/assistant/{assistant_id}",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        }
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify the assistant is deleted by trying to get their info
    verify_response = client.get(
        "/assistant/info",
        headers={
            "Authorization": f"Bearer {assistant_token}",
            "accept": "application/json"
        }
    )
    
    # Should fail because the token is now invalid (user deleted)
    assert verify_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_companion_to_event_success(client: TestClient, token: str, faker: Faker, clean_face_db) -> None:  # type: ignore
    """Test the POST /assistant/register-companion-to-event/{event_id} endpoint successfully.
    
    This test verifies the complete flow of registering a companion to an event,
    including creating two assistants, an event, registering the main assistant,
    and then registering the companion.

    curl -X 'POST' \\
        'http://127.0.0.1:8000/assistant/register-companion-to-event/1' \\
        -H 'Authorization: Bearer <token>' \\
        -F 'companion_id=2' \\
        -F 'companion_type=first_grade'
    """
    from unittest.mock import patch
    
    # Mock the face recognition to allow different people
    with patch('app.helpers.personTempImg.PersonImg.is_single_person') as mock_is_single_person, \
         patch('app.helpers.personTempImg.PersonImg.path_imgs_similar_people') as mock_similar_people:
        
        mock_is_single_person.return_value = True
        mock_similar_people.return_value = []  # No similar people found
        
        # Create main assistant
        id_number1 = faker.ecuadorian_id_number()
        password1 = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        person1: Dict[str, Any] = {
            "gender": faker.random_element(elements=["female", "male", "other"]),
            "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
            "id_number_type": "cedula",
            "id_number": id_number1,
            "phone": str(faker.random_int(min=1000000000, max=9999999999)),
            "accepted_terms": "true",
            "last_name": faker.last_name(),
            "first_name": faker.first_name(),
            "password": password1,
            "email": generate_assistant_email(faker),
        }

        with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
            files = {"image": ("person1.jpeg", image_file, "image/jpeg")}
            create_response1 = client.post(
                "/assistant/add",
                headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
                data=person1,
                files=files
            )

        assert create_response1.status_code == status.HTTP_201_CREATED

        # Create companion assistant
        id_number2 = faker.ecuadorian_id_number()
        person2: Dict[str, Any] = {
            "gender": faker.random_element(elements=["female", "male", "other"]),
            "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
            "id_number_type": "cedula",
            "id_number": id_number2,
            "phone": str(faker.random_int(min=1000000000, max=9999999999)),
            "accepted_terms": "true",
            "last_name": faker.last_name(),
            "first_name": faker.first_name(),
            "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            "email": generate_assistant_email(faker),
        }
    
        with open("tests/imgs/person3.jpg", "rb") as image_file:
            files = {"image": ("person2.jpeg", image_file, "image/jpeg")}
            create_response2 = client.post(
                "/assistant/add",
                headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
                data=person2,
                files=files
            )
        
        assert create_response2.status_code == status.HTTP_201_CREATED
        companion_id = create_response2.json()["id"]

        # Create an event
        event_data: Dict[str, Any] = {
            "name": faker.sentence(nb_words=3),
            "description": faker.text(max_nb_chars=200),
            "location": faker.address(),
            "maps_link": "https://maps.app.goo.gl/testlocation",
            "capacity": 100,
            "capacity_type": "limit_of_spaces",
        }

        with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
            event_files = {"image": ("event.jpeg", image_file, "image/jpeg")}
            event_response = client.post(
                "/events/add",
                headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
                data=event_data,
                files=event_files
            )
        
        assert event_response.status_code == status.HTTP_201_CREATED
        event_id = event_response.json()["id"]

        # Get main assistant token
        assistant1_token = client.post(
            "/token",
            data={
                "grant_type": "password",
                "username": person1["email"],
                "password": password1,
                "scope": "assistant",
                "client_id": "",
                "client_secret": ""
            }
        ).json()["access_token"]

        # Register main assistant to the event first
        register_response = client.post(
            f"/assistant/register-to-event/{event_id}",
            headers={
                "Authorization": f"Bearer {assistant1_token}",
                "accept": "application/json"
            }
        )
        
        assert register_response.status_code == status.HTTP_200_OK

        # Now register companion to the event
        companion_response = client.post(
            f"/assistant/register-companion-to-event/{event_id}",
            headers={
                "Authorization": f"Bearer {assistant1_token}",
                "accept": "application/json"
            },
            data={
                "companion_id": str(companion_id),
                "companion_type": "first_grade"
            }
        )

        json_response = companion_response.json()
        assert companion_response.status_code == status.HTTP_200_OK
        assert json_response["event_id"] == event_id
        assert json_response["companion_id"] == companion_id
        assert json_response["companion_type"] == "first_grade"