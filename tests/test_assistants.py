from fastapi import status
from fastapi.testclient import TestClient


# def test_add_assistant_success(client: TestClient, token: str):
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

#     response = client.post(
#         "/assistant/add",
#         headers={
#             "Authorization": f"Bearer {token}",
#             "accept": "application/json"},
#         data={
#             "gender": "female",
#             "date_of_birth": "1997-09-19",
#             "id_number_type": "cedula",
#             "id_number": "1709690034",
#             "phone": "0999999999",
#             "accepted_terms": "true",
#             "last_name": "Mebarak",
#             "first_name": "Shakira",
#             "password": "ShakiraShakir34@",
#             "email": "alphawolf@gmail.com"
#         },
#     )

#     json_response = response.json()

#     assert response.status_code == status.HTTP_200_OK
#     assert json_response["email"] == "alphawolf@gmail.com"
#     assert json_response["first_name"] == "Shakira"
#     assert json_response["last_name"] == "Mebarak"
#     assert json_response["role"] == "assistant"
#     assert json_response["assistant"]["gender"] == "female"
#     assert json_response["assistant"]["accepted_terms"] is True


# def test_add_assistant_duplicate_email(client: TestClient, token: str):
#     """Test the POST /assistant/add endpoint with a duplicate email.

#     curl -X 'POST' \\
#       'http://127.0.0.1:8000/assistant/add' \\
#       -H 'accept: application/json' \\
#       -H 'Content-Type: multipart/form-data' \\
#       -F 'email=alphawolf@gmail.com' ...
#     """

#     client.post(
#         "/assistant/add",
#         headers={
#             "Authorization": f"Bearer {token}",
#             "accept": "application/json"},
#         data={
#             "gender": "female",
#             "date_of_birth": "1997-09-19",
#             "id_number_type": "cedula",
#             "id_number": "1709690034",
#             "phone": "0999999999",
#             "accepted_terms": "true",
#             "last_name": "Mebarak",
#             "first_name": "Shakira",
#             "password": "ShakiraShakir34@",
#             "email": "alphawolf@gmail.com"
#         },
#     )

#     duplicate_response = client.post(
#         "/assistant/add",
#         headers={"accept": "application/json"},
#         data={
#             "gender": "female",
#             "date_of_birth": "1997-09-19",
#             "id_number_type": "cedula",
#             "id_number": "1709690034",
#             "phone": "0999999999",
#             "accepted_terms": "true",
#             "last_name": "Mebarak",
#             "first_name": "Shakira",
#             "password": "ShakiraShakir34@",
#             "email": "alphawolf@gmail.com"
#         },
#     )

#     json_response = duplicate_response.json()

#     assert duplicate_response.status_code == status.HTTP_409_CONFLICT
#     assert "Duplicate entry" in json_response["detail"]


# def test_add_assistant_invalid_id_number(client: TestClient, token: str):
#     """Test the POST /assistant/add endpoint with an invalid Ecuadorian ID number.

#     curl -X 'POST' \\
#       'http://127.0.0.1:8000/assistant/add' \\
#       -F 'id_number=1701698834' ...
#     """

#     response = client.post(
#         "/assistant/add",
#         headers={
#             "Authorization": f"Bearer {token}",
#             "accept": "application/json"},
#         data={
#             "gender": "female",
#             "date_of_birth": "1997-09-19",
#             "id_number_type": "cedula",
#             "id_number": "1701698834",
#             "phone": "0999999999",
#             "accepted_terms": "true",
#             "last_name": "Mebarak",
#             "first_name": "Shakira",
#             "password": "ShakiraShakir34@",
#             "email": "alphawolf@gmail.com"
#         },
#     )

#     json_response = response.json()

#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     assert json_response["detail"][0]["msg"] == "Value error, Invalid Ecuadorian ID number"


def test_add_assistant_without_accepting_terms(client: TestClient, token: str):
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
            "password": "ShakiraShakir34@",
            "email": "alphawolf@gmail.com"
        },
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert json_response["detail"][0]["loc"] == ["body", "accepted_terms"]
    assert json_response["detail"][0]["msg"] == "Value error, You must accept the terms and conditions."


def test_add_assistant_with_future_birthdate(client: TestClient, token: str):
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
            "password": "ShakiraShakir34@",
            "email": "alphawolf@gmail.com"
        },
    )

    json_response = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert json_response["detail"][0]["loc"] == ["body", "date_of_birth"]
    assert json_response["detail"][0]["msg"] == "Value error, Date must be before today."

# Assistants get by image

# Assistants get by id number


# def test_get_assistant_by_id_number(client: TestClient, token: str):
#     """Test the GET /assistant/get-by-id-number/{id_number} endpoint with a valid ID.

#     curl -X 'GET' \\
#       'http://127.0.0.1:8000/assistant/get-by-id-number/1709690034' \\
#       -H 'accept: application/json'
#     """
#     image_content = b"imagebytes"
#     files = {
#         "image": ("Shakira1.jpeg", image_content, "image/jpeg")
#     }

#     # First, create the assistant
#     create_response = client.post(
#         "/assistant/add",
#         headers={
#             "Authorization": f"Bearer {token}",
#             "accept": "application/json"
#         },
#         data={
#             "gender": "female",
#             "date_of_birth": "1997-09-19",
#             "id_number_type": "cedula",
#             "id_number": "1709690034",
#             "phone": "0999999999",
#             "accepted_terms": "true",
#             "last_name": "Mebarak",
#             "first_name": "Shakira",
#             "password": "ShakiraShakir34@",
#             "email": "alphawolf@gmail.com"
#         },
#         files=files
#     )

#     assert create_response.status_code == status.HTTP_200_OK

#     response = client.get(
#         "/assistant/get-by-id-number/1709690034",
#         headers={"accept": "application/json"}
#     )

#     json_response = response.json()

#     assert response.status_code == status.HTTP_200_OK
#     assert json_response["assistant"]["id_number"] == "1709690034"
#     assert json_response["first_name"] == "Shakira"
#     assert json_response["last_name"] == "Mebarak"
#     assert json_response["email"] == "alphawolf@gmail.com"


def test_get_assistant_by_id_number_not_found(client: TestClient, token: str):
    """Test the GET /assistant/get-by-id-number/{id_number} endpoint with a non-existing ID.

    curl -X 'GET' \\
      'http://127.0.0.1:8000/assistant/get-by-id-number/1726754301' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer <token>'
    """
    response = client.get(
        "/assistant/get-by-id-number/1726754301",
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
