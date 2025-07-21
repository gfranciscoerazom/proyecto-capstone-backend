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


def test_add_staff_to_event_success(session: Session, client: TestClient, faker: Faker):
    """Test adding staff to event successfully."""
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()
    session.refresh(organizer)
    
    # Create staff member
    staff = User(
        first_name="Staff",
        last_name="Member",
        email="staff@udla.edu.ec", 
        hashed_password=get_password_hash("password123"),
        role=Role.STAFF,
    )
    session.add(staff)
    session.commit()
    session.refresh(staff)
    
    # Create event
    from app.db.database import Event
    from app.models.TypeCapacity import TypeCapacity
    from uuid import uuid4
    
    event = Event(
        name="Test Event",
        description="Test Description",
        location="Test Location",
        maps_link="https://maps.app.goo.gl/test",
        capacity=100,
        capacity_type=TypeCapacity.LIMIT_OF_SPACES,
        image_uuid=uuid4(),
        organizer_id=organizer.id or 1,
    )
    session.add(event)
    session.commit()
    session.refresh(event)

    response = client.post(
        "/staff/add-staff-to-event",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "staff_id": str(staff.id),
            "event_id": str(event.id),
        }
    )

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["id"] == event.id
    assert len(json_response["staff"]) == 1
    assert json_response["staff"][0]["id"] == staff.id


def test_add_staff_to_event_staff_not_found(session: Session, client: TestClient):
    """Test adding non-existent staff to event."""
    # Create organizer and event
    organizer = User(
        first_name="Admin",
        last_name="User", 
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()
    session.refresh(organizer)
    
    from app.db.database import Event
    from app.models.TypeCapacity import TypeCapacity
    from uuid import uuid4
    
    event = Event(
        name="Test Event",
        description="Test Description", 
        location="Test Location",
        maps_link="https://maps.app.goo.gl/test",
        capacity=100,
        capacity_type=TypeCapacity.LIMIT_OF_SPACES,
        image_uuid=uuid4(),
        organizer_id=organizer.id or 1,
    )
    session.add(event)
    session.commit()
    session.refresh(event)

    response = client.post(
        "/staff/add-staff-to-event",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "staff_id": "99999",  # Non-existent staff ID
            "event_id": str(event.id),
        }
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response["detail"] == "Staff not found"


def test_add_staff_to_event_user_not_staff(session: Session, client: TestClient):
    """Test adding non-staff user to event."""
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()
    session.refresh(organizer)
    
    # Create another organizer (not staff)
    other_organizer = User(
        first_name="Other",
        last_name="Organizer",
        email="other@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.ORGANIZER,  # Not STAFF
    )
    session.add(other_organizer)
    session.commit()
    session.refresh(other_organizer)
    
    # Create event
    from app.db.database import Event
    from app.models.TypeCapacity import TypeCapacity
    from uuid import uuid4
    
    event = Event(
        name="Test Event",
        description="Test Description",
        location="Test Location", 
        maps_link="https://maps.app.goo.gl/test",
        capacity=100,
        capacity_type=TypeCapacity.LIMIT_OF_SPACES,
        image_uuid=uuid4(),
        organizer_id=organizer.id or 1,
    )
    session.add(event)
    session.commit()
    session.refresh(event)

    response = client.post(
        "/staff/add-staff-to-event",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "staff_id": str(other_organizer.id),
            "event_id": str(event.id),
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json_response = response.json()
    assert json_response["detail"] == "User is not a staff"


def test_add_staff_to_event_event_not_found(session: Session, client: TestClient):
    """Test adding staff to non-existent event."""
    # Create staff member
    staff = User(
        first_name="Staff",
        last_name="Member",
        email="staff@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.STAFF,
    )
    session.add(staff)
    session.commit()
    session.refresh(staff)

    response = client.post(
        "/staff/add-staff-to-event",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "staff_id": str(staff.id),
            "event_id": "99999",  # Non-existent event ID
        }
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response["detail"] == "Event not found"


def test_get_my_events_success(session: Session, client: TestClient):
    """Test getting staff member's assigned events."""
    # Create staff member
    staff = User(
        first_name="Staff",
        last_name="Member",
        email="staff@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.STAFF,
    )
    session.add(staff)
    session.commit()
    session.refresh(staff)
    
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec", 
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()
    session.refresh(organizer)
    
    # Create event and assign staff
    from app.db.database import Event
    from app.models.TypeCapacity import TypeCapacity
    from uuid import uuid4
    
    event = Event(
        name="Test Event",
        description="Test Description",
        location="Test Location",
        maps_link="https://maps.app.goo.gl/test",
        capacity=100,
        capacity_type=TypeCapacity.LIMIT_OF_SPACES,
        image_uuid=uuid4(),
        organizer_id=organizer.id or 1,
    )
    event.staff.append(staff)
    session.add(event)
    session.commit()
    session.refresh(event)

    # Get token for staff
    token = client.post("/token", data={
        "grant_type": "password",
        "username": "staff@udla.edu.ec",
        "password": "password123",
        "scope": "staff",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.get(
        "/staff/my-events",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert len(json_response) == 1
    assert json_response[0]["id"] == event.id
    assert json_response[0]["name"] == "Test Event"


def test_get_my_events_no_events(session: Session, client: TestClient):
    """Test getting events for staff with no assigned events."""
    # Create staff member
    staff = User(
        first_name="Staff",
        last_name="Member",
        email="staff@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.STAFF,
    )
    session.add(staff)
    session.commit()

    # Get token for staff
    token = client.post("/token", data={
        "grant_type": "password",
        "username": "staff@udla.edu.ec",
        "password": "password123",
        "scope": "staff",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.get(
        "/staff/my-events",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response["detail"] == "No events found for the current staff member"


def test_get_all_staff_success(session: Session, client: TestClient):
    """Test getting all staff members."""
    # Create multiple staff members
    staff1 = User(
        first_name="Staff",
        last_name="One",
        email="staff1@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.STAFF,
    )
    staff2 = User(
        first_name="Staff",
        last_name="Two",
        email="staff2@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.STAFF,
    )
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    
    session.add(staff1)
    session.add(staff2)
    session.add(organizer)
    session.commit()

    response = client.get("/staff/all")

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert len(json_response) == 2
    
    # Check that only staff members are returned
    staff_emails = [staff["email"] for staff in json_response]
    assert "staff1@udla.edu.ec" in staff_emails
    assert "staff2@udla.edu.ec" in staff_emails
    assert "admin@udla.edu.ec" not in staff_emails


def test_get_all_staff_empty(session: Session, client: TestClient):
    """Test getting all staff when no staff exists."""
    # Create organizer but no staff
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()

    response = client.get("/staff/all")

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert len(json_response) == 0


def test_update_staff_success(session: Session, client: TestClient):
    """Test updating staff member successfully."""
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()
    
    # Create staff member
    staff = User(
        first_name="Staff",
        last_name="Member",
        email="staff@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.STAFF,
    )
    session.add(staff)
    session.commit()
    session.refresh(staff)

    # Get token for organizer
    token = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.patch(
        f"/staff/{staff.id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "first_name": "Updated",
            "last_name": "Name",
        }
    )

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["first_name"] == "Updated"
    assert json_response["last_name"] == "Name"
    assert json_response["email"] == "staff@udla.edu.ec"  # Should remain unchanged


def test_update_staff_not_found(session: Session, client: TestClient):
    """Test updating non-existent staff member."""
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()

    # Get token for organizer
    token = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.patch(
        "/staff/99999",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "first_name": "Updated",
        }
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response["detail"] == "Staff member not found"


def test_update_staff_user_not_staff(session: Session, client: TestClient):
    """Test updating user who is not staff."""
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()
    
    # Create another organizer (not staff)
    other_organizer = User(
        first_name="Other",
        last_name="Organizer",
        email="other@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.ORGANIZER,
    )
    session.add(other_organizer)
    session.commit()
    session.refresh(other_organizer)

    # Get token for organizer
    token = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.patch(
        f"/staff/{other_organizer.id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "first_name": "Updated",
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json_response = response.json()
    assert json_response["detail"] == "User is not a staff member"


def test_update_staff_with_password(session: Session, client: TestClient):
    """Test updating staff member's password."""
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()
    
    # Create staff member
    staff = User(
        first_name="Staff",
        last_name="Member",
        email="staff@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.STAFF,
    )
    session.add(staff)
    session.commit()
    session.refresh(staff)

    # Get token for organizer
    token = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.patch(
        f"/staff/{staff.id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "password": "NewPassword123@",
        }
    )

    assert response.status_code == status.HTTP_200_OK
    
    # Verify password was updated by trying to login with new password
    login_response = client.post("/token", data={
        "grant_type": "password",
        "username": "staff@udla.edu.ec",
        "password": "NewPassword123@",
        "scope": "staff",
        "client_id": "",
        "client_secret": ""
    })
    
    assert login_response.status_code == status.HTTP_200_OK


def test_delete_staff_success(session: Session, client: TestClient):
    """Test deleting staff member successfully."""
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()
    
    # Create staff member
    staff = User(
        first_name="Staff",
        last_name="Member",
        email="staff@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.STAFF,
    )
    session.add(staff)
    session.commit()
    session.refresh(staff)

    # Get token for organizer
    token = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.delete(
        f"/staff/{staff.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify staff was deleted
    deleted_staff = session.get(User, staff.id)
    assert deleted_staff is None


def test_delete_staff_not_found(session: Session, client: TestClient):
    """Test deleting non-existent staff member."""
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()

    # Get token for organizer
    token = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.delete(
        "/staff/99999",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response["detail"] == "Staff member not found"


def test_delete_staff_user_not_staff(session: Session, client: TestClient):
    """Test deleting user who is not staff."""
    # Create organizer
    organizer = User(
        first_name="Admin",
        last_name="User",
        email="admin@udla.edu.ec",
        hashed_password=get_password_hash("admin"),
        role=Role.ORGANIZER,
    )
    session.add(organizer)
    session.commit()
    
    # Create another organizer (not staff)
    other_organizer = User(
        first_name="Other",
        last_name="Organizer",
        email="other@udla.edu.ec",
        hashed_password=get_password_hash("password123"),
        role=Role.ORGANIZER,
    )
    session.add(other_organizer)
    session.commit()
    session.refresh(other_organizer)

    # Get token for organizer
    token = client.post("/token", data={
        "grant_type": "password",
        "username": "admin@udla.edu.ec",
        "password": "admin",
        "scope": "organizer",
        "client_id": "",
        "client_secret": ""
    }).json()["access_token"]

    response = client.delete(
        f"/staff/{other_organizer.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json_response = response.json()
    assert json_response["detail"] == "User is not a staff member"
