import smtplib
import ssl
import datetime
from email.message import EmailMessage
from typing import Any

from fastapi.templating import Jinja2Templates

from app.db.database import Event, EventDate, User
from app.settings.config import settings

templates = Jinja2Templates(directory="app/html/emails")


def connect_to_smtp_server():
    """Establish and return a connection to the SMTP server."""
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context)
    server.login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD)
    return server


def _send_email(user: User, subject: str, template_name: str, template_vars: dict[str, Any]) -> None:
    template = templates.get_template(template_name)  # type: ignore
    body = template.render(**template_vars)  # type: ignore

    em = EmailMessage()
    em['From'] = settings.EMAIL_SENDER
    em['To'] = user.email
    em['Subject'] = subject
    em.set_content(body, subtype='html')

    with connect_to_smtp_server() as server:
        server.sendmail(settings.EMAIL_SENDER, user.email, em.as_string())


def send_new_assistant_email(
    user: User
) -> None:
    subject = f"Bienvenido {user.first_name} {user.last_name}!"
    _send_email(
        user,
        subject,
        "account_creation.html",
        {"first_name": user.first_name}
    )


def send_event_rating_email(
    user: User
) -> None:
    subject = f"¿Qué te pareció el evento {user.first_name} {user.last_name}?"
    _send_email(
        user,
        subject,
        "event_rating.html",
        {"first_name": user.first_name}
    )


def send_event_registration_email(
    user: User,
    event: Event,
    dates: list[EventDate]
) -> None:
    subject = f"Hola {user.first_name} {user.last_name}, estás oficialmente registrado/a!"
    event_date = sorted(dates, key=lambda d: d.day_date)[0]
    _send_email(
        user,
        subject,
        "event_registration.html",
        {
            "event_name": event.name,
            "day_date": event_date.day_date.strftime("%d/%m/%Y"),
            "start_time": event_date.start_time,
            "end_time": event_date.end_time,
            "event_location": event.location,
        }
    )


def send_event_reminder_email(
    user: User,
    event: Event,
    dates: list[EventDate]
) -> None:
    subject = f"Hola {user.first_name} {user.last_name}, te recordamos que del evento '{event.name}' en UDLA ya es mañana"
    event_date = sorted(dates, key=lambda d: d.day_date)[0]
    _send_email(
        user,
        subject,
        "event_reminder.html",
        {
            "first_name": user.first_name,
            "event_name": event.name,
            "day_date": event_date.day_date.strftime("%d/%m/%Y"),
            "start_time": event_date.start_time,
            "end_time": event_date.end_time,
            "event_location": event.location,
        }
    )


# def send_registration_canceled_email(
#     user: User,
#     event: Event
# ) -> None:
#     subject = f"Cancelaste el evento '{event.name}' en la UDLA"
#     _send_email(
#         user,
#         subject,
#         "registration_canceled.html",
#         {"first_name": user.first_name}
#     )


def send_registration_canceled_email(
    user: User,
    event: Event,
) -> None:
    subject = f"Cancelaste el evento '{event.name}' en la UDLA"
    _send_email(
        user,
        subject,
        "registration_canceled.html",
        {
            "first_name": user.first_name,
            "event_name": event.name,
        }
    )