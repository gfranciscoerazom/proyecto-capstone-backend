import tempfile
import uuid
from pathlib import Path

from deepface import DeepFace  # type: ignore
from fastapi import UploadFile
from sqlmodel import Session

from app.db.database import Assistant, AssistantCreate, User, UserCreate
from app.models.Role import Role
from app.settings.config import settings


class PersonImg:
    """
    Class to handle image processing for person recognition.
    """

    def __init__(self, img: UploadFile):
        """
        Initializes the PersonImg class with an image.
        The image is validated to ensure it contains exactly one person.

        :param self: Self reference
        :type self: PersonImg
        :param img: Image file to be processed
        :type img: UploadFile
        """
        if not self.is_single_person(img):
            raise ValueError(
                "Face could not be detected in the image or many faces detected. Please ensure the image contains exactly one person."
            )

        self.img: UploadFile = img

    @staticmethod
    def is_single_person(img: UploadFile) -> bool:
        """
        Checks if the image contains exactly one person.

        :param img: Image file to be processed
        :type img: UploadFile
        :return: True if the image contains exactly one person, False otherwise
        :rtype: bool
        """
        # Create a temporary file to store the uploaded image
        img.file.seek(0)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(img.file.read())
            temp_file_path = temp_file.name

        # Extract faces from the image
        try:
            face_objs = DeepFace.extract_faces(  # type: ignore
                img_path=temp_file_path,
                detector_backend="yunet",
                align=True,
            )
        except ValueError:
            return False
        finally:
            # Clean up the temporary file
            Path(temp_file_path).unlink()

        return len(face_objs) == 1

    def path_imgs_similar_people(self) -> list[Path]:
        """
        Finds similar people in the image database using the provided image.

        :param self: Self reference
        :type self: PersonImg
        :return: List of paths to similar people images
        :rtype: list[Path]
        """
        # Create a temporary file to store the uploaded image
        # This is necessary because the file pointer is at the end after reading
        self.img.file.seek(0)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(self.img.file.read())
            temp_file_path = temp_file.name

        # Find similar people in the image database
        try:
            similar_people = DeepFace.find(  # type: ignore
                img_path=temp_file_path,
                db_path="./data/people_imgs",
                model_name=settings.FACE_RECOGNITION_AI_MODEL,
                threshold=settings.FACE_RECOGNITION_AI_THRESHOLD,
                detector_backend="yunet",
                enforce_detection=False,
            )[0]["identity"].to_list()
        finally:
            # Clean up the temporary file
            Path(temp_file_path).unlink()

        return [Path(path) for path in similar_people]  # type: ignore

    def person_already_exists(self) -> bool:
        """
        Checks if the person already exists in the image database.

        :param self: Self reference
        :type self: PersonImg
        :return: True if the person already exists, False otherwise
        :rtype: bool
        """
        return len(self.path_imgs_similar_people()) > 0

    def save(self, user: UserCreate, assistant: AssistantCreate, session: Session) -> User:
        """
        Saves the image to image database if the person does not already exist and also saves the user and assistant information because
        the image is related to them.

        :param self: Self reference
        :type self: PersonImg

        :param user: User information
        :type user: UserCreate

        :param assistant: Assistant information
        :type assistant: AssistantCreate

        :param session: Database session
        :type session: Session

        :return: Path to the saved image
        :rtype: Path

        :raises ValueError: If the person already exists in the database
        :raises Exception: If the image cannot be saved
        :raises IntegrityError: If there is a database integrity error
        """
        if self.person_already_exists():
            raise ValueError(
                "The person already exists in the database. Please enter a different person."
            )
        image_uuid: uuid.UUID = uuid.uuid4()

        # Save the user and assistant information
        hashed_password: bytes = user.get_password_hash()

        extra_data_user: dict[str, bytes | Role] = {
            "hashed_password": hashed_password,
            "role": Role.ASSISTANT,
        }

        extra_data_assistant: dict[str, uuid.UUID] = {
            "image_uuid": image_uuid,
        }

        db_user: User = User.model_validate(user, update=extra_data_user)
        db_assistant: Assistant = Assistant.model_validate(
            assistant,
            update=extra_data_assistant
        )

        db_user.assistant = db_assistant

        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        # Save the image to the image database
        new_img_path = Path(
            f"./data/people_imgs/{image_uuid}.png"
        )

        new_img_path.parent.mkdir(parents=True, exist_ok=True)
        self.img.file.seek(0)
        with new_img_path.open("wb") as image_file:
            image_file.write(self.img.file.read())

        return db_user
