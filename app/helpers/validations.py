from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.database import Event, EventDate


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


def is_valid_ecuadorian_passport_number(passport_number: str) -> bool:
    """
    Validates an Ecuadorian passport number.

    Args:
        passport_number (str): The passport number to validate.

    Returns:
        bool: True if the passport number is valid, False otherwise.
    """
    return bool(re.match(r"^A\d{7}$", passport_number))


def are_unique_dates(event: Event, dates: list[EventDate] | EventDate) -> bool:
    """
    Checks if the dates to be added to an event are unique.

    Args:
        event (Event): The event to add dates to.
        dates (list[EventDate]): The list of dates to be added.

    Returns:
        bool: True if the dates are unique, False otherwise.
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
