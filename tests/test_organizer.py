import pytest
from fastapi import status
from fastapi.testclient import TestClient
from faker import Faker

from app.db.database import User, UserCreate, UserUpdate
from app.models.Role import Role
from app.models.FaceRecognitionAiModel import FaceRecognitionAiModel


# Test fixtures for creating test users
@pytest.fixture
def test_organizer_data(faker: Faker) -> dict:
    """Create test data for organizer creation."""
    return {
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "email": faker.email(domain="udla.edu.ec"),
        "password": faker.password(),
        "id_number": faker.ecuadorian_id_number(),
        "phone": faker.phone_number()[:15]  # Limit phone number length
    }


@pytest.fixture
def another_organizer(session, faker: Faker) -> User:
    """Create another organizer user for testing."""
    from app.security.security import get_password_hash
    
    organizer = User(
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        email=faker.email(domain="udla.edu.ec"),
        hashed_password=get_password_hash(faker.password()),
        role=Role.ORGANIZER,
        id_number=faker.ecuadorian_id_number(),
        phone=faker.phone_number()[:15]
    )
    session.add(organizer)
    session.commit()
    session.refresh(organizer)
    return organizer


@pytest.fixture
def staff_user(session, faker: Faker) -> User:
    """Create a staff user for testing."""
    from app.security.security import get_password_hash
    
    staff = User(
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        email=faker.email(domain="udla.edu.ec"),
        hashed_password=get_password_hash(faker.password()),
        role=Role.STAFF,
        id_number=faker.ecuadorian_id_number(),
        phone=faker.phone_number()[:15]
    )
    session.add(staff)
    session.commit()
    session.refresh(staff)
    return staff


# Tests for POST /organizer/add endpoint
class TestAddOrganizer:
    """Test cases for adding organizers."""

    def test_add_organizer_success(self, client: TestClient, token: str, test_organizer_data: dict):
        """Test successful organizer creation."""
        response = client.post(
            "/organizer/add",
            data=test_organizer_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        json_response = response.json()
        assert json_response["email"] == test_organizer_data["email"]
        assert json_response["first_name"] == test_organizer_data["first_name"]
        assert json_response["last_name"] == test_organizer_data["last_name"]
        assert json_response["role"] == Role.ORGANIZER
        assert "password" not in json_response
        assert "hashed_password" not in json_response

    def test_add_organizer_duplicate_email(self, client: TestClient, token: str, test_organizer_data: dict):
        """Test adding organizer with duplicate email fails."""
        # First creation should succeed
        response1 = client.post(
            "/organizer/add",
            data=test_organizer_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second creation with same email should fail
        response2 = client.post(
            "/organizer/add",
            data=test_organizer_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response2.json()["detail"]

    def test_add_organizer_without_auth(self, client: TestClient, test_organizer_data: dict):
        """Test adding organizer without authentication fails."""
        response = client.post("/organizer/add", data=test_organizer_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_organizer_invalid_token(self, client: TestClient, test_organizer_data: dict):
        """Test adding organizer with invalid token fails."""
        response = client.post(
            "/organizer/add",
            data=test_organizer_data,
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_organizer_missing_required_fields(self, client: TestClient, token: str):
        """Test adding organizer with missing required fields fails."""
        incomplete_data = {
            "first_name": "John",
            # Missing required fields
        }
        response = client.post(
            "/organizer/add",
            data=incomplete_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Tests for PATCH /organizer/change-settings endpoint
class TestChangeSettings:
    """Test cases for changing face recognition settings."""

    def test_change_model_only(self, client: TestClient):
        """Test changing only the face recognition model."""
        response = client.patch(
            "/organizer/change-settings",
            params={"model_name": FaceRecognitionAiModel.FACENET}
        )
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response["model"] == FaceRecognitionAiModel.FACENET

    def test_change_threshold_only(self, client: TestClient):
        """Test changing only the threshold."""
        response = client.patch(
            "/organizer/change-settings",
            params={"threshold": 0.8}
        )
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response["threshold"] == 0.8

    def test_change_both_model_and_threshold(self, client: TestClient):
        """Test changing both model and threshold."""
        response = client.patch(
            "/organizer/change-settings",
            params={
                "model_name": FaceRecognitionAiModel.DEEPFACE,
                "threshold": 0.9
            }
        )
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response["model"] == FaceRecognitionAiModel.DEEPFACE
        assert json_response["threshold"] == 0.9

    def test_reset_threshold(self, client: TestClient):
        """Test resetting threshold to default."""
        response = client.patch(
            "/organizer/change-settings",
            params={"threshold": 0}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_change_settings_no_params(self, client: TestClient):
        """Test calling change settings with no parameters."""
        response = client.patch("/organizer/change-settings")
        assert response.status_code == status.HTTP_200_OK

    def test_change_settings_all_models(self, client: TestClient):
        """Test changing to each available face recognition model."""
        for model in FaceRecognitionAiModel:
            response = client.patch(
                "/organizer/change-settings",
                params={"model_name": model}
            )
            assert response.status_code == status.HTTP_200_OK
            json_response = response.json()
            assert json_response["model"] == model


# Tests for GET /organizer/get-settings endpoint
class TestGetSettings:
    """Test cases for getting face recognition settings."""

    def test_get_settings_success(self, client: TestClient):
        """Test successful retrieval of settings."""
        response = client.get("/organizer/get-settings")
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert "model" in json_response
        assert "threshold" in json_response

    def test_get_settings_after_change(self, client: TestClient):
        """Test getting settings after changing them."""
        # Change settings first
        client.patch(
            "/organizer/change-settings",
            params={
                "model_name": FaceRecognitionAiModel.ARCFACE,
                "threshold": 0.7
            }
        )
        
        # Get settings
        response = client.get("/organizer/get-settings")
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response["model"] == FaceRecognitionAiModel.ARCFACE
        assert json_response["threshold"] == 0.7


# Tests for GET /organizer/all endpoint
class TestListOrganizers:
    """Test cases for listing all organizers."""

    def test_list_organizers_success(self, client: TestClient, admin_user: tuple[User, str], another_organizer: User):
        """Test successful retrieval of all organizers."""
        response = client.get("/organizer/all")
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert isinstance(json_response, list)
        assert len(json_response) >= 2  # At least admin_user and another_organizer
        
        # Check that all returned users are organizers
        for organizer in json_response:
            assert organizer["role"] == Role.ORGANIZER

    def test_list_organizers_excludes_non_organizers(self, client: TestClient, admin_user: tuple[User, str], staff_user: User):
        """Test that list organizers doesn't include non-organizer users."""
        response = client.get("/organizer/all")
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        
        # Check that staff user is not in the list
        staff_emails = [org["email"] for org in json_response]
        assert staff_user.email not in staff_emails

    def test_list_organizers_empty_list(self, client: TestClient, session):
        """Test listing organizers when there are none."""
        # Delete all organizers
        session.query(User).filter(User.role == Role.ORGANIZER).delete()
        session.commit()
        
        response = client.get("/organizer/all")
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response == []


# Tests for PATCH /organizer/{organizer_id} endpoint
class TestUpdateOrganizer:
    """Test cases for updating organizers."""

    def test_update_organizer_success(self, client: TestClient, token: str, another_organizer: User, faker: Faker):
        """Test successful organizer update."""
        update_data = {
            "first_name": faker.first_name(),
            "last_name": faker.last_name()
        }
        
        response = client.patch(
            f"/organizer/{another_organizer.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response["first_name"] == update_data["first_name"]
        assert json_response["last_name"] == update_data["last_name"]
        assert json_response["email"] == another_organizer.email  # Unchanged

    def test_update_organizer_password(self, client: TestClient, token: str, another_organizer: User, faker: Faker):
        """Test updating organizer password."""
        update_data = {"password": faker.password()}
        
        response = client.patch(
            f"/organizer/{another_organizer.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert "password" not in json_response
        assert "hashed_password" not in json_response

    def test_update_organizer_email_conflict(self, client: TestClient, token: str, admin_user: tuple[User, str], another_organizer: User):
        """Test updating organizer with existing email fails."""
        update_data = {"email": admin_user[0].email}
        
        response = client.patch(
            f"/organizer/{another_organizer.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "ya existe" in response.json()["detail"]

    def test_update_nonexistent_organizer(self, client: TestClient, token: str):
        """Test updating non-existent organizer fails."""
        update_data = {"first_name": "New Name"}
        
        response = client.patch(
            "/organizer/99999",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "no encontrado" in response.json()["detail"]

    def test_update_non_organizer_user(self, client: TestClient, token: str, staff_user: User):
        """Test updating non-organizer user fails."""
        update_data = {"first_name": "New Name"}
        
        response = client.patch(
            f"/organizer/{staff_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no es un organizador" in response.json()["detail"]

    def test_update_organizer_without_auth(self, client: TestClient, another_organizer: User):
        """Test updating organizer without authentication fails."""
        update_data = {"first_name": "New Name"}
        
        response = client.patch(
            f"/organizer/{another_organizer.id}",
            json=update_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Tests for DELETE /organizer/{organizer_id} endpoint
class TestDeleteOrganizer:
    """Test cases for deleting organizers."""

    def test_delete_organizer_success(self, client: TestClient, token: str, another_organizer: User):
        """Test successful organizer deletion."""
        response = client.delete(
            f"/organizer/{another_organizer.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_nonexistent_organizer(self, client: TestClient, token: str):
        """Test deleting non-existent organizer fails."""
        response = client.delete(
            "/organizer/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "no encontrado" in response.json()["detail"]

    def test_delete_non_organizer_user(self, client: TestClient, token: str, staff_user: User):
        """Test deleting non-organizer user fails."""
        response = client.delete(
            f"/organizer/{staff_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no es un organizador" in response.json()["detail"]

    def test_delete_self(self, client: TestClient, token: str, admin_user: tuple[User, str]):
        """Test organizer cannot delete themselves."""
        response = client.delete(
            f"/organizer/{admin_user[0].id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No puedes eliminarte a ti mismo" in response.json()["detail"]

    def test_delete_organizer_without_auth(self, client: TestClient, another_organizer: User):
        """Test deleting organizer without authentication fails."""
        response = client.delete(f"/organizer/{another_organizer.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_organizer_invalid_token(self, client: TestClient, another_organizer: User):
        """Test deleting organizer with invalid token fails."""
        response = client.delete(
            f"/organizer/{another_organizer.id}",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Integration tests
class TestOrganizerIntegration:
    """Integration tests for organizer workflows."""

    def test_full_organizer_lifecycle(self, client: TestClient, token: str, test_organizer_data: dict, faker: Faker):
        """Test complete organizer lifecycle: create, read, update, delete."""
        # Create organizer
        create_response = client.post(
            "/organizer/add",
            data=test_organizer_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        organizer_id = create_response.json()["id"]
        
        # List organizers and verify creation
        list_response = client.get("/organizer/all")
        assert list_response.status_code == status.HTTP_200_OK
        organizer_emails = [org["email"] for org in list_response.json()]
        assert test_organizer_data["email"] in organizer_emails
        
        # Update organizer
        update_data = {"first_name": faker.first_name()}
        update_response = client.patch(
            f"/organizer/{organizer_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["first_name"] == update_data["first_name"]
        
        # Delete organizer
        delete_response = client.delete(
            f"/organizer/{organizer_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        final_list_response = client.get("/organizer/all")
        final_organizer_emails = [org["email"] for org in final_list_response.json()]
        assert test_organizer_data["email"] not in final_organizer_emails

    def test_settings_persistence(self, client: TestClient):
        """Test that settings changes persist across get requests."""
        # Change settings
        change_response = client.patch(
            "/organizer/change-settings",
            params={
                "model_name": FaceRecognitionAiModel.DLIB,
                "threshold": 0.85
            }
        )
        assert change_response.status_code == status.HTTP_200_OK
        
        # Get settings multiple times to ensure persistence
        for _ in range(3):
            get_response = client.get("/organizer/get-settings")
            assert get_response.status_code == status.HTTP_200_OK
            settings = get_response.json()
            assert settings["model"] == FaceRecognitionAiModel.DLIB
            assert settings["threshold"] == 0.85
