from fastapi import status
from fastapi.testclient import TestClient


def test_get_organizer_info(client: TestClient, token: str):
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

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["email"] == "admin@udla.edu.ec"
    assert json_response["first_name"] == "Admin"
    assert json_response["last_name"] == "User"
    assert json_response["role"] == "organizer"
