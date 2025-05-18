from __future__ import annotations

import re
import uuid
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from deepface import DeepFace  # type: ignore
from fastapi import HTTPException, UploadFile, status

from app.helpers.dateAndTime import get_quito_time

if TYPE_CHECKING:
    from app.db.database import Event, EventDate


def password_validator(password: str) -> str:
    """
    Checks if the password meets the required security criteria.

    A valid password must have at least 9 characters, 1 lowercase letter, 1 uppercase letter, 1 digit, and 1 special character.

    :param password: Password to be validated
    :type password: str
    :return: The validated password
    :rtype: str
    :raises ValueError: If the password does not meet the criteria
    """
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
    """
    Checks if the image contains exactly one person.

    :param image_path: Path to the image file
    :type image_path: Path
    :return: True if the image contains exactly one person, False otherwise
    :rtype: bool
    :raises ValueError: If face detection fails for reasons other than no face found
    """
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
    """
    Saves an uploaded image to a specified folder and returns its UUID.

    :param image: The image file to save
    :type image: UploadFile
    :param folder: The folder where the image will be saved
    :type folder: str
    :return: The UUID of the saved image
    :rtype: UUID
    """
    image_uuid: UUID = uuid.uuid4()
    image_path: Path = Path(
        f"./data/{folder}/{image_uuid}.png"
    )
    image_path.parent.mkdir(parents=True, exist_ok=True)

    with image_path.open("wb") as image_file:
        image_file.write(await image.read())

    return image_uuid


async def save_user_image(image: UploadFile, folder: str = "people_imgs") -> UUID:
    """
    Saves a user image after validating it contains exactly one person.

    :param image: The image file to save
    :type image: UploadFile
    :param folder: The folder where the image will be saved (default: "people_imgs")
    :type folder: str, optional
    :return: The UUID of the saved image
    :rtype: UUID
    :raises HTTPException: If the image does not contain exactly one person
    """
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
    """
    Checks if the given date is before or equal to today.

    :param date: Date to be validated
    :type date: date
    :return: The validated date
    :rtype: date
    :raises ValueError: If the date is after today
    """
    if date > get_quito_time().date():
        raise ValueError("Date must be before today.")
    return date


def is_after_today(date: date) -> date:
    """
    Checks if the given date is after or equal to today.

    :param date: Date to be validated
    :type date: date
    :return: The validated date
    :rtype: date
    :raises ValueError: If the date is before today
    """
    if date < get_quito_time().date():
        raise ValueError("Date must be after today.")
    return date


def is_valid_phone_number(phone_number: str) -> str:
    """
    Checks if the phone number is valid (10 digits).

    :param phone_number: Phone number to be validated
    :type phone_number: str
    :return: The validated phone number
    :rtype: str
    :raises ValueError: If the phone number is not valid
    """
    if not (len(phone_number) == 10 and phone_number.isdigit()):
        raise ValueError("Phone number must have 10 digits.")
    return phone_number


def is_accepted_terms(accepted_terms: bool) -> bool:
    """
    Checks if the terms and conditions have been accepted.

    :param accepted_terms: Whether the terms have been accepted
    :type accepted_terms: bool
    :return: The validated acceptance
    :rtype: bool
    :raises ValueError: If the terms have not been accepted
    """
    if not accepted_terms:
        raise ValueError("You must accept the terms and conditions.")
    return accepted_terms


def is_valid_google_maps_url(url: str) -> str:
    """
    Validates a Google Maps URL.

    A valid URL must start with "https://maps.app.goo.gl/".


    :param url: The URL to validate
    :type url: str
    :return: The validated URL
    :rtype: str
    :raises ValueError: If the URL is not valid
    """
    if not url.startswith("https://maps.app.goo.gl/"):
        raise ValueError("URL must be a valid Google Maps URL.")
    return url


def is_valid_ecuadorian_id(id_number: str) -> bool:
    """
    Validates an Ecuadorian identification number.

    A valid ID must have 10 digits, a valid province code, and a correct check digit.

    :param id_number: The identification number to validate
    :type id_number: str
    :return: True if the identification number is valid, False otherwise
    :rtype: bool
    """
    # Check if the ID length is 10
    if len(id_number) != 10:
        return False

    # Check if the first two digits are between 1 and 24
    province_code = int(id_number[:2])
    if province_code < 1 or province_code > 24:
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


def is_valid_ecuadorian_passport_number(passport_number: str) -> bool:
    """
    Validates an Ecuadorian passport number.

    A valid passport number starts with 'A' followed by 7 digits.

    :param passport_number: The passport number to validate
    :type passport_number: str
    :return: True if the passport number is valid, False otherwise
    :rtype: bool
    """
    return bool(re.match(r"^A\d{7}$", passport_number))


def are_unique_dates(event: Event, dates: list[EventDate] | EventDate) -> bool:
    """
    Checks if the dates to be added to an event are unique.

    :param event: The event to add dates to
    :type event: Event
    :param dates: The list of dates to be added
    :type dates: list[EventDate] or EventDate
    :return: True if the dates are unique, False otherwise
    :rtype: bool
    """
    if not isinstance(dates, list):
        dates = [dates]

    existing_event_dates: list[EventDate] = event.event_dates.copy()
    dates = dates.copy()

    for date in dates:
        if date in existing_event_dates:
            return False
        existing_event_dates.append(date)

    return True


def is_a_person_name(name: str) -> str:
    """Checks if the name is a valid person name.

    A valid person name cannot be empty, cannot consist of only numbers, and needs to begin with a capital letter.

    :param name: Name to be validated
    :type name: str
    :return: The validated name
    :rtype: str
    :raises ValueError: If the name is invalid
    """
    name = name.strip()

    if not name:
        raise ValueError("Name cannot be empty.")

    if name.isdigit():
        raise ValueError("Name cannot consist of only numbers.")

    if not name[0].isupper():
        raise ValueError("Name must begin with a capital letter.")

    return name
