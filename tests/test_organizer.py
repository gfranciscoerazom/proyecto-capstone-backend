from fastapi import status
from fastapi.testclient import TestClient

from app.db.database import User


def test_get_organizer_info(client: TestClient, token: str, admin_user: tuple[User, str]):
    """Test the organizer info endpoint with valid token.

    The curl command to test this endpoint is:

    curl -X 'GET' \\
      'http://127.0.0.1:8000/info' \\
      -H 'accept: application/json' \\
      -H 'Authorization: Bearer {token}'
    """
    response = client.get("/info", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["email"] == admin_user[0].email
    assert json_response["first_name"] == admin_user[0].first_name
    assert json_response["last_name"] == admin_user[0].last_name
    assert json_response["role"] == admin_user[0].role
