import pytest
import shutil
import tempfile
from pathlib import Path
from faker import Faker
from faker.providers import BaseProvider
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db.database import User, get_session
from app.main import app
from app.models.Role import Role
from app.security.security import get_password_hash


class EcuadorProvider(BaseProvider):
    def ecuadorian_id_number(self) -> str:
        # Genera una cédula ecuatoriana válida (10 dígitos, con verificación simple)
        from random import randint

        def calculate_verifier(digits: str) -> int:
            coef = [2, 1, 2, 1, 2, 1, 2, 1, 2]
            total = 0
            for i in range(9):
                val = int(digits[i]) * coef[i]
                if val > 9:
                    val -= 9
                total += val
            verifier = 10 - (total % 10)
            return 0 if verifier == 10 else verifier

        province = f"{randint(1,24):02d}"
        middle = f"{randint(1000000, 9999999)}"
        base = province + middle[:7]
        verifier = calculate_verifier(base)
        return base + str(verifier)


@pytest.fixture(name="faker")
def faker():
    fake = Faker()
    fake.add_provider(EcuadorProvider)
    return fake


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        return session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="admin_user")
def admin_user_fixture(session: Session, faker: Faker):
    password = faker.password()
    user = User(
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        email=faker.email(domain="udla.edu.ec"),
        hashed_password=get_password_hash(password),
        role=Role.ORGANIZER,
    )

    session.add(user)
    session.commit()

    return user, password


@pytest.fixture(name="token")
def token_fixture(client: TestClient, admin_user: tuple[User, str]):
    token = client.post(
        "/token",
        data={
            "grant_type": "password",
            "username": admin_user[0].email,
            "password": admin_user[1],
            "scope": "organizer",
            "client_id": "",
            "client_secret": ""
        }
    ).json()["access_token"]

    return token


@pytest.fixture(name="clean_face_db")
def clean_face_db_fixture():
    """Clean up face recognition database before each test."""
    import os
    from app.settings.config import settings
    
    def clean_directory(path: Path):
        """Helper function to clean a directory."""
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
            except OSError:
                import time
                time.sleep(0.1)
                try:
                    shutil.rmtree(path)
                except OSError:
                    pass
        path.mkdir(parents=True, exist_ok=True)
    
    # Get the actual DATA_FOLDER from settings
    try:
        data_folder = getattr(settings, 'DATA_FOLDER', 'data')
    except:
        data_folder = 'data'
    
    # Clean up various possible face recognition database locations
    paths_to_clean = [
        Path("./data/people_imgs"),
        Path("data/people_imgs"),
        Path(f"{data_folder}/people_imgs"),
    ]
    
    for people_imgs_path in paths_to_clean:
        clean_directory(people_imgs_path)
    
    # Clean up any DeepFace model cache files
    try:
        temp_dir = Path(tempfile.gettempdir())
        for pattern in ["*facenet*.pkl", "*ds_model*.pkl", "*representations*.pkl"]:
            for pkl_file in temp_dir.glob(pattern):
                try:
                    pkl_file.unlink()
                except OSError:
                    pass
    except Exception:
        pass
        
    yield
    
    # Cleanup after test
    for people_imgs_path in paths_to_clean:
        if people_imgs_path.exists():
            try:
                shutil.rmtree(people_imgs_path)
            except OSError:
                pass



