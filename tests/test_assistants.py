from pathlib import Path

from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient


# def test_add_assistant_success(client: TestClient, token: str, faker: Faker):
#     """Test the POST /assistant/add endpoint with valid input.

#     curl -X 'POST' \\
#       'http://127.0.0.1:8000/assistant/add' \\
#       -H 'accept: application/json' \\
#       -H 'Content-Type: multipart/form-data' \\
#       -F 'gender=female' \\
#       -F 'date_of_birth=1997-09-19' \\
#       -F 'id_number_type=cedula' \\
#       -F 'id_number=1709690034' \\
#       -F 'phone=0999999999' \\
#       -F 'accepted_terms=true' \\
#       -F 'last_name=Mebarak' \\
#       -F 'first_name=Shakira' \\
#       -F 'image=@Shakira1.jpeg;type=image/jpeg' \\
#       -F 'password=ShakiraShakir34@' \\
#       -F 'email=alphawolf@gmail.com'
#     """

#     id_number_type = faker.random_element(elements=["cedula", "passport"])
#     id_number = str(faker.ecuadorian_id_number(
#     )) if id_number_type == "cedula" else f"A{faker.random_int(min=1000000, max=9999999)}"

#     person = {
#         "gender": faker.random_element(elements=["female", "male", "other"]),
#         "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
#         "id_number_type": id_number_type,
#         "id_number": id_number,
#         "phone": str(faker.random_int(min=1000000000, max=9999999999)),
#         "accepted_terms": "true",
#         "last_name": faker.last_name(),
#         "first_name": faker.first_name(),
#         "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
#         "email": faker.email(),
#     }

#     with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
#         files = {
#             "image": ("person.jpeg", image_file, "image/jpeg")
#         }

#         response = client.post(
#             "/assistant/add",
#             headers={
#                 "Authorization": f"Bearer {token}",
#                 "accept": "application/json"},
#             data=person,
#             files=files
#         )

#     json_response = response.json()

#     assert response.status_code == status.HTTP_201_CREATED
#     assert json_response["email"] == person["email"]
#     assert json_response["first_name"] == person["first_name"]
#     assert json_response["last_name"] == person["last_name"]
#     assert json_response["role"] == "assistant"
#     assert json_response["assistant"]["gender"] == person["gender"]
#     assert json_response["assistant"]["accepted_terms"] is True

#     image_uuid = json_response["assistant"]["image_uuid"]
#     image = Path("data/people_imgs") / f"{image_uuid}.png"

#     assert image.exists(), "Image file was not created."

#     if image.exists():
#         image.unlink()


# def test_add_assistant_duplicate_email(client: TestClient, token: str, faker: Faker):
#     """Test the POST /assistant/add endpoint with a duplicate email.

#     curl -X 'POST' \\
#       'http://127.0.0.1:8000/assistant/add' \\
#       -H 'accept: application/json' \\
#       -H 'Content-Type: multipart/form-data' \\
#       -F 'email=alphawolf@gmail.com' ...
#     """
#     person_1 = {
#         "gender": "male",
#         "date_of_birth": "1997-09-19",
#         "id_number_type": "cedula",
#         "id_number": "1709690034",
#         "phone": "0999999999",
#         "accepted_terms": "true",
#         "last_name": "Alvarez",
#         "first_name": "Alfredo",
#         "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
#         "email": "alphawolf@gmail.com",
#     }

#     person_2 = {
#         "gender": "female",
#         "date_of_birth": "1999-10-25",
#         "id_number_type": "cedula",
#         "id_number": "1750319731",
#         "phone": "0999999998",
#         "accepted_terms": "true",
#         "last_name": "Mebarak",
#         "first_name": "Shakira",
#         "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
#         "email": "alphawolf@gmail.com",
#     }

#     with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
#         files = {
#             "image": ("person.jpeg", image_file, "image/jpeg")
#         }

#         response_1 = client.post(
#             "/assistant/add",
#             headers={
#                 "Authorization": f"Bearer {token}",
#                 "accept": "application/json"},
#             data=person_1,
#             files=files
#         )

#     with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
#         files = {
#             "image": ("person.jpeg", image_file, "image/jpeg")
#         }

#         response_2 = client.post(
#             "/assistant/add",
#             headers={
#                 "Authorization": f"Bearer {token}",
#                 "accept": "application/json"},
#             data=person_2,
#             files=files
#         )

#     json_response_2 = response_2.json()

#     assert response_2.status_code == status.HTTP_409_CONFLICT
#     assert "UNIQUE constraint failed: user.email" in json_response_2["detail"]

#     json_response_1 = response_1.json()
#     image_uuid = json_response_1["assistant"]["image_uuid"]
#     image = Path("data/people_imgs") / f"{image_uuid}.png"

#     assert image.exists(), "Image file was not created."

#     if image.exists():
#         image.unlink()


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

# Assistants get by image

# Assistants get by id number


# def test_get_assistant_by_id_number(client: TestClient, token: str, faker: Faker):
#     """Test the GET /assistant/get-by-id-number/{id_number} endpoint with a valid ID.

#     curl -X 'GET' \\
#       'http://127.0.0.1:8000/assistant/get-by-id-number/1709690034' \\
#       -H 'accept: application/json'
#     """
#     id_number_type = faker.random_element(elements=["cedula", "passport"])
#     id_number = str(faker.ecuadorian_id_number(
#     )) if id_number_type == "cedula" else f"A{faker.random_int(min=1000000, max=9999999)}"

#     person = {
#         "gender": faker.random_element(elements=["female", "male", "other"]),
#         "date_of_birth": faker.date_of_birth(minimum_age=18, maximum_age=60).strftime("%Y-%m-%d"),
#         "id_number_type": id_number_type,
#         "id_number": id_number,
#         "phone": str(faker.random_int(min=1000000000, max=9999999999)),
#         "accepted_terms": "true",
#         "last_name": faker.last_name(),
#         "first_name": faker.first_name(),
#         "password": faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
#         "email": faker.email(),
#     }

#     with open("tests/imgs/foto_carne.jpg", "rb") as image_file:
#         files = {
#             "image": ("person.jpeg", image_file, "image/jpeg")
#         }

#         client.post(
#             "/assistant/add",
#             headers={
#                 "Authorization": f"Bearer {token}",
#                 "accept": "application/json"},
#             data=person,
#             files=files
#         )

#     response = client.get(
#         f"/assistant/get-by-id-number/{id_number}",
#         headers={"accept": "application/json"}
#     )

#     json_response = response.json()

#     assert response.status_code == status.HTTP_200_OK
#     assert json_response["assistant"]["id_number"] == id_number
#     assert json_response["first_name"] == person["first_name"]
#     assert json_response["last_name"] == person["last_name"]
#     assert json_response["email"] == person["email"]

#     image_uuid = json_response["assistant"]["image_uuid"]
#     image = Path("data/people_imgs") / f"{image_uuid}.png"

#     assert image.exists(), "Image file was not created."

#     if image.exists():
#         image.unlink()


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


# Assistants image

# Assistants register to event

# Assistants register companion to event
