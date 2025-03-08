import re
import uuid
from datetime import date
from pathlib import Path
from typing import Annotated
from uuid import UUID

from deepface import DeepFace  # type: ignore
from fastapi import HTTPException, UploadFile, status
from pydantic import AfterValidator

from app.helpers.dateAndTime import get_quito_time


def password_validator(password: str) -> str:
    if (
        len(password) < 9 or
        len(re.findall(r"[a-z]", password)) < 1 or
        len(re.findall(r"[A-Z]", password)) < 1 or
        len(re.findall(r"\d", password)) < 1 or
        len(re.findall(r"[¡!@#$%^¿?&*()\-_+./\\]", password)) < 1
    ):
        raise ValueError(
            "Password must have at least 9 characters, 1 lowercase letters, 1 uppercase letters, 1 digit, and 1 special character."
        )
    return password


def is_single_person(image_path: Path) -> bool:
    """Checks if image contains a single person."""
    try:
        face_objs = DeepFace.extract_faces(  # type: ignore
            img_path=str(image_path),
            detector_backend="yunet",
            align=True,
        )
    except ValueError as e:
        if "Face could not be detected" in str(e):
            return False
        raise e
    return len(face_objs) == 1


async def save_image(image: UploadFile, folder: str) -> UUID:
    """Saves image and returns UUID."""
    image_uuid: UUID = uuid.uuid4()
    image_path: Path = Path(
        f"./data/{folder}/{image_uuid}.png"
    )
    image_path.parent.mkdir(parents=True, exist_ok=True)

    with image_path.open("wb") as image_file:
        image_file.write(await image.read())

    return image_uuid


async def save_user_image(image: UploadFile, folder: str = "people_imgs") -> UUID:
    """Saves user image and returns UUID."""
    image_uuid: UUID = await save_image(image, folder)
    image_path: Path = Path(f"./data/{folder}/{image_uuid}.png")

    if not is_single_person(image_path):
        if image_path.exists():
            image_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The image must contain exactly one person",
        )
    return image_uuid


def is_before_today(date: date) -> date:
    if date > get_quito_time().date():
        raise ValueError("Date must be before today.")
    return date


def is_after_today(date: date) -> date:
    if date < get_quito_time().date():
        raise ValueError("Date must be after today.")
    return date


def is_valid_phone_number(phone_number: str) -> str:
    if not (len(phone_number) == 10 and phone_number.isdigit()):
        raise ValueError("Phone number must have 10 digits.")
    return phone_number


def is_accepted_terms(accepted_terms: bool) -> bool:
    if not accepted_terms:
        raise ValueError("You must accept the terms and conditions.")
    return accepted_terms


def is_valid_google_maps_url(url: str) -> str:
    if not url.startswith("https://maps.app.goo.gl/"):
        raise ValueError("URL must be a valid Google Maps URL.")
    return url


Password = Annotated[
    str,
    AfterValidator(password_validator)
]

BeforeTodayDate = Annotated[
    date,
    AfterValidator(is_before_today)
]

AfterTodayDate = Annotated[
    date,
    AfterValidator(is_after_today)
]

PhoneNumber = Annotated[
    str,
    AfterValidator(is_valid_phone_number)
]


TermsAndConditions = Annotated[
    bool,
    AfterValidator(is_accepted_terms)
]


GoogleMapsURL = Annotated[
    str,
    AfterValidator(is_valid_google_maps_url)
]

UpperStr = Annotated[
    str,
    AfterValidator(str.upper)
]
