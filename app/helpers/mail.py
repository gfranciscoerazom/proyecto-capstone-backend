import smtplib
import ssl
from email.message import EmailMessage

from fastapi.templating import Jinja2Templates

from app.db.database import Event, User
from app.settings.config import settings

templates = Jinja2Templates(directory="app/html/emails")


def connect_to_smtp_server():
    """Establish and return a connection to the SMTP server."""
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context)
    server.login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD)
    return server


def send_new_assistant_email(
    user: User
) -> None:
    subject = f"Bienvenido {user.first_name} {user.last_name}!"
    template = templates.get_template("account_creation.html")  # type: ignore
    body = template.render(  # type: ignore
        first_name=user.first_name,
    )

    em = EmailMessage()
    em['From'] = settings.EMAIL_SENDER
    em['To'] = user.email
    em['Subject'] = subject
    em.set_content(body, subtype='html')

    with connect_to_smtp_server() as server:
        server.sendmail(settings.EMAIL_SENDER, user.email, em.as_string())

   
def send_event_rating_email(
    user: User
) -> None:
    subject = f"¿Qué te pareció el evento {user.first_name} {user.last_name}?"
    template = templates.get_template("event_rating.html")  # type: ignore
    body = template.render(  # type: ignore
        first_name=user.first_name,
    )

    em = EmailMessage()
    em['From'] = settings.EMAIL_SENDER
    em['To'] = user.email
    em['Subject'] = subject
    em.set_content(body, subtype='html')

    with connect_to_smtp_server() as server:
        server.sendmail(settings.EMAIL_SENDER, user.email, em.as_string())

def send_event_registration_email(
    user: User
) -> None:
    subject = f"Hola {user.first_name} {user.last_name}, estas oficialmente registrado/a!"
    template = templates.get_template("event_registration.html")  # type: ignore
    body = template.render(  # type: ignore
    )

    em = EmailMessage()
    em['From'] = settings.EMAIL_SENDER
    em['To'] = user.email
    em['Subject'] = subject
    em.set_content(body, subtype='html')

    with connect_to_smtp_server() as server:
        server.sendmail(settings.EMAIL_SENDER, user.email, em.as_string())         

def send_event_reminder_email(
    user: User,
    event: Event
) -> None:
    subject = f"Recordatorio del evento '{event.name}' en UDLA"
    template = templates.get_template("event_reminder.html")  # type: ignore
    body = template.render(  # type: ignore
        first_name=user.first_name,
    )

    em = EmailMessage()
    em['From'] = settings.EMAIL_SENDER
    em['To'] = user.email
    em['Subject'] = subject
    em.set_content(body, subtype='html')

    with connect_to_smtp_server() as server:
        server.sendmail(settings.EMAIL_SENDER, user.email, em.as_string())  

def send_registration_canceled_email(
    user: User,
    event: Event
) -> None:
    subject = f"Cancelaste el evento '{event.name}' en la UDLA"
    template = templates.get_template("registration_canceled.html")  # type: ignore
    body = template.render(  # type: ignore
        first_name=user.first_name,
    )

    em = EmailMessage()
    em['From'] = settings.EMAIL_SENDER
    em['To'] = user.email
    em['Subject'] = subject
    em.set_content(body, subtype='html')

    with connect_to_smtp_server() as server:
        server.sendmail(settings.EMAIL_SENDER, user.email, em.as_string())                    

