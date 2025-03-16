import smtplib
import ssl
from email.message import EmailMessage

from app.db.database import User
from app.settings.config import settings


def send_new_assistant_email(
    user: User
) -> None:
    subject = f"Bienvenido {user.first_name} {user.last_name}!"
    body = f"""
    <h1>Te damos la bienvenida a nuestra plataforma de eventos</h1>

    Bienvenido {user.first_name} {user.last_name}!
    """
    em = EmailMessage()
    em['From'] = settings.EMAIL_SENDER
    em['To'] = user.email
    em['Subject'] = subject
    em.set_content(body, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD)
        server.sendmail(settings.EMAIL_SENDER, user.email, em.as_string())
