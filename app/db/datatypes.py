from datetime import date
from typing import Annotated

from pydantic import AfterValidator

from app.helpers.validations import (is_a_person_name, is_accepted_terms,
                                     is_after_today, is_before_today,
                                     is_valid_google_maps_url,
                                     is_valid_phone_number, password_validator)

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

PersonName = Annotated[
    str,
    AfterValidator(is_a_person_name)
]
