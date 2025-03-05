import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID

from deepface import DeepFace  # type: ignore
from fastapi import HTTPException, UploadFile, status
from pydantic import AfterValidator


def is_valid_ecuadorian_id(id_number: str) -> bool:
    """
    Validates an Ecuadorian identification number.

    Args:
        id_number (str): The identification number to validate.

    Returns:
        bool: True if the identification number is valid, False otherwise.
    """
    # Check if the ID length is 10
    if len(id_number) != 10:
        return False

    # Check if the first two digits are between 0 and 24
    province_code = int(id_number[:2])
    if province_code < 0 or province_code > 24:
        return False

    # Check if the third character is a digit
    if not id_number[2].isdigit():
        return False

    # Validate the check digit
    coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for i in range(9):
        product = int(id_number[i]) * coefficients[i]
        if product >= 10:
            product -= 9
        total += product

    check_digit = (10 - (total % 10)) % 10
    return check_digit == int(id_number[9])


def is_valid_ecuadorian_passport(passport_number: str) -> bool:
    """
    Validates an Ecuadorian passport number.

    Args:
        passport_number (str): The passport number to validate.

    Returns:
        bool: True if the passport number is valid, False otherwise.
    """
    return bool(re.match(r"^A\d{7}$", passport_number))


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
    if date > datetime.now().date():
        raise ValueError("Date must be before today.")
    return date


def is_after_today(date: date) -> date:
    if date < datetime.now().date():
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
