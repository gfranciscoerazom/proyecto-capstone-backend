import pytest
import smtplib
import ssl
from datetime import date, time
from email.message import EmailMessage
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from faker import Faker

from app.db.database import User, Event, EventDate
from app.helpers.mail import (
    connect_to_smtp_server,
    _send_email,
    send_new_assistant_email,
    send_event_rating_email,
    send_event_registration_email,
    send_event_reminder_email,
    send_registration_canceled_email
)
from app.models.Role import Role
from app.models.TypeCapacity import TypeCapacity


class TestConnectToSmtpServer:
    """Tests for the connect_to_smtp_server function."""

    @patch('app.helpers.mail.ssl.create_default_context')
    @patch('app.helpers.mail.smtplib.SMTP_SSL')
    @patch('app.helpers.mail.settings')
    def test_connect_to_smtp_server_success(self, mock_settings, mock_smtp, mock_ssl):
        """Test successful SMTP server connection."""
        # Arrange
        mock_settings.EMAIL_SENDER = "test@example.com"
        mock_settings.EMAIL_APP_PASSWORD = "app_password"
        mock_context = Mock()
        mock_ssl.return_value = mock_context
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        # Act
        result = connect_to_smtp_server()

        # Assert
        mock_ssl.assert_called_once()
        mock_smtp.assert_called_once_with('smtp.gmail.com', 465, context=mock_context)
        mock_server.login.assert_called_once_with("test@example.com", "app_password")
        assert result == mock_server

    @patch('app.helpers.mail.ssl.create_default_context')
    @patch('app.helpers.mail.smtplib.SMTP_SSL')
    @patch('app.helpers.mail.settings')
    def test_connect_to_smtp_server_login_failure(self, mock_settings, mock_smtp, mock_ssl):
        """Test SMTP server connection with login failure."""
        # Arrange
        mock_settings.EMAIL_SENDER = "test@example.com"
        mock_settings.EMAIL_APP_PASSWORD = "wrong_password"
        mock_context = Mock()
        mock_ssl.return_value = mock_context
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value = mock_server

        # Act & Assert
        with pytest.raises(smtplib.SMTPAuthenticationError):
            connect_to_smtp_server()


class TestSendEmail:
    """Tests for the _send_email function."""

    def create_test_user(self, faker: Faker) -> User:
        """Helper method to create a test user."""
        return User(
            id=1,
            email=faker.email(),
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )

    @patch('app.helpers.mail.connect_to_smtp_server')
    @patch('app.helpers.mail.templates')
    @patch('app.helpers.mail.settings')
    def test_send_email_success(self, mock_settings, mock_templates, mock_connect, faker: Faker):
        """Test successful email sending."""
        # Arrange
        mock_settings.EMAIL_SENDER = "sender@example.com"
        user = self.create_test_user(faker)
        subject = "Test Subject"
        template_name = "test_template.html"
        template_vars = {"name": "John"}
        
        mock_template = Mock()
        mock_template.render.return_value = "<html>Test Email Body</html>"
        mock_templates.get_template.return_value = mock_template
        
        mock_server = Mock()
        mock_connect.return_value.__enter__.return_value = mock_server

        # Act
        _send_email(user, subject, template_name, template_vars)

        # Assert
        mock_templates.get_template.assert_called_once_with(template_name)
        mock_template.render.assert_called_once_with(**template_vars)
        mock_server.sendmail.assert_called_once()
        
        # Verify email content
        call_args = mock_server.sendmail.call_args[0]
        assert call_args[0] == "sender@example.com"
        assert call_args[1] == user.email

    @patch('app.helpers.mail.connect_to_smtp_server')
    @patch('app.helpers.mail.templates')
    @patch('app.helpers.mail.settings')
    def test_send_email_template_error(self, mock_settings, mock_templates, mock_connect, faker: Faker):
        """Test email sending with template error."""
        # Arrange
        user = self.create_test_user(faker)
        mock_templates.get_template.side_effect = Exception("Template not found")

        # Act & Assert
        with pytest.raises(Exception, match="Template not found"):
            _send_email(user, "Subject", "nonexistent.html", {})

    @patch('app.helpers.mail.connect_to_smtp_server')
    @patch('app.helpers.mail.templates')
    @patch('app.helpers.mail.settings')
    def test_send_email_smtp_error(self, mock_settings, mock_templates, mock_connect, faker: Faker):
        """Test email sending with SMTP error."""
        # Arrange
        user = self.create_test_user(faker)
        
        mock_template = Mock()
        mock_template.render.return_value = "<html>Test</html>"
        mock_templates.get_template.return_value = mock_template
        
        mock_server = Mock()
        mock_server.sendmail.side_effect = smtplib.SMTPException("SMTP Error")
        mock_connect.return_value.__enter__.return_value = mock_server

        # Act & Assert
        with pytest.raises(smtplib.SMTPException):
            _send_email(user, "Subject", "template.html", {})


class TestSendNewAssistantEmail:
    """Tests for the send_new_assistant_email function."""

    @patch('app.helpers.mail._send_email')
    def test_send_new_assistant_email_success(self, mock_send_email, faker: Faker):
        """Test successful new assistant email sending."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="Juan",
            last_name="Pérez",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )

        # Act
        send_new_assistant_email(user)

        # Assert
        mock_send_email.assert_called_once_with(
            user,
            "Bienvenido Juan Pérez!",
            "account_creation.html",
            {"first_name": "Juan"}
        )

    @patch('app.helpers.mail._send_email')
    def test_send_new_assistant_email_with_special_characters(self, mock_send_email, faker: Faker):
        """Test new assistant email with special characters in name."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="María José",
            last_name="Rodríguez-García",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )

        # Act
        send_new_assistant_email(user)

        # Assert
        mock_send_email.assert_called_once_with(
            user,
            "Bienvenido María José Rodríguez-García!",
            "account_creation.html",
            {"first_name": "María José"}
        )


class TestSendEventRatingEmail:
    """Tests for the send_event_rating_email function."""

    @patch('app.helpers.mail._send_email')
    def test_send_event_rating_email_success(self, mock_send_email, faker: Faker):
        """Test successful event rating email sending."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="Ana",
            last_name="González",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )

        # Act
        send_event_rating_email(user)

        # Assert
        mock_send_email.assert_called_once_with(
            user,
            "¿Qué te pareció el evento Ana González?",
            "event_rating.html",
            {"first_name": "Ana"}
        )


class TestSendEventRegistrationEmail:
    """Tests for the send_event_registration_email function."""

    def create_test_event(self, faker: Faker) -> Event:
        """Helper method to create a test event."""
        return Event(
            id=1,
            name=faker.text(max_nb_chars=50),
            description=faker.text(),
            location=faker.address(),
            maps_link="https://maps.app.goo.gl/example",
            capacity=100,
            capacity_type=TypeCapacity.SITE_CAPACITY,
            image_uuid=uuid4(),
            organizer_id=1
        )

    def create_test_event_date(self, event_id: int = 1) -> EventDate:
        """Helper method to create a test event date."""
        return EventDate(
            id=1,
            event_id=event_id,
            day_date=date(2025, 8, 15),
            start_time=time(10, 0),
            end_time=time(12, 0)
        )

    @patch('app.helpers.mail._send_email')
    def test_send_event_registration_email_success(self, mock_send_email, faker: Faker):
        """Test successful event registration email sending."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="Carlos",
            last_name="López",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )
        event = self.create_test_event(faker)
        event.name = "Conferencia de Tecnología"
        event.location = "Auditorio Principal UDLA"
        
        dates = [self.create_test_event_date()]

        # Act
        send_event_registration_email(user, event, dates)

        # Assert
        mock_send_email.assert_called_once_with(
            user,
            "Hola Carlos López, estás oficialmente registrado/a!",
            "event_registration.html",
            {
                "event_name": "Conferencia de Tecnología",
                "day_date": "15/08/2025",
                "start_time": time(10, 0),
                "end_time": time(12, 0),
                "event_location": "Auditorio Principal UDLA",
            }
        )

    @patch('app.helpers.mail._send_email')
    def test_send_event_registration_email_empty_dates(self, mock_send_email, faker: Faker):
        """Test event registration email with empty dates list."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="Laura",
            last_name="Martínez",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )
        event = self.create_test_event(faker)
        dates = []

        # Act
        send_event_registration_email(user, event, dates)

        # Assert
        mock_send_email.assert_not_called()

    @patch('app.helpers.mail._send_email')
    def test_send_event_registration_email_multiple_dates(self, mock_send_email, faker: Faker):
        """Test event registration email with multiple dates (should use earliest)."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="Roberto",
            last_name="Silva",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )
        event = self.create_test_event(faker)
        event.name = "Workshop de Python"
        
        date1 = EventDate(
            id=1,
            event_id=1,
            day_date=date(2025, 8, 20),  # Later date
            start_time=time(14, 0),
            end_time=time(16, 0)
        )
        date2 = EventDate(
            id=2,
            event_id=1,
            day_date=date(2025, 8, 15),  # Earlier date
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        dates = [date1, date2]

        # Act
        send_event_registration_email(user, event, dates)

        # Assert
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        template_vars = call_args[3]
        assert template_vars["day_date"] == "15/08/2025"  # Should use earlier date


class TestSendEventReminderEmail:
    """Tests for the send_event_reminder_email function."""

    def create_test_event(self, faker: Faker) -> Event:
        """Helper method to create a test event."""
        return Event(
            id=1,
            name=faker.text(max_nb_chars=50),
            description=faker.text(),
            location=faker.address(),
            maps_link="https://maps.app.goo.gl/example",
            capacity=100,
            capacity_type=TypeCapacity.SITE_CAPACITY,
            image_uuid=uuid4(),
            organizer_id=1
        )

    @patch('app.helpers.mail._send_email')
    def test_send_event_reminder_email_success(self, mock_send_email, faker: Faker):
        """Test successful event reminder email sending."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="Patricia",
            last_name="Vega",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )
        event = self.create_test_event(faker)
        event.name = "Seminario de Innovación"
        event.location = "Sala de Conferencias B"
        
        event_date = EventDate(
            id=1,
            event_id=1,
            day_date=date(2025, 9, 10),
            start_time=time(9, 30),
            end_time=time(11, 30)
        )
        dates = [event_date]

        # Act
        send_event_reminder_email(user, event, dates)

        # Assert
        mock_send_email.assert_called_once_with(
            user,
            "Hola Patricia Vega, te recordamos que del evento 'Seminario de Innovación' en UDLA ya es mañana",
            "event_reminder.html",
            {
                "first_name": "Patricia",
                "event_name": "Seminario de Innovación",
                "day_date": "10/09/2025",
                "start_time": time(9, 30),
                "end_time": time(11, 30),
                "event_location": "Sala de Conferencias B",
            }
        )

    @patch('app.helpers.mail._send_email')
    def test_send_event_reminder_email_with_sorting(self, mock_send_email, faker: Faker):
        """Test event reminder email with multiple dates (should use earliest)."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="Diego",
            last_name="Morales",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )
        event = self.create_test_event(faker)
        event.name = "Hackathon 2025"
        
        # Create dates in reverse chronological order
        date1 = EventDate(
            id=1,
            event_id=1,
            day_date=date(2025, 10, 25),
            start_time=time(16, 0),
            end_time=time(18, 0)
        )
        date2 = EventDate(
            id=2,
            event_id=1,
            day_date=date(2025, 10, 20),
            start_time=time(8, 0),
            end_time=time(10, 0)
        )
        dates = [date1, date2]

        # Act
        send_event_reminder_email(user, event, dates)

        # Assert
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        template_vars = call_args[3]
        assert template_vars["day_date"] == "20/10/2025"  # Should use earlier date


class TestSendRegistrationCanceledEmail:
    """Tests for the send_registration_canceled_email function."""

    def create_test_event(self, faker: Faker) -> Event:
        """Helper method to create a test event."""
        return Event(
            id=1,
            name=faker.text(max_nb_chars=50),
            description=faker.text(),
            location=faker.address(),
            maps_link="https://maps.app.goo.gl/example",
            capacity=100,
            capacity_type=TypeCapacity.SITE_CAPACITY,
            image_uuid=uuid4(),
            organizer_id=1
        )

    @patch('app.helpers.mail._send_email')
    def test_send_registration_canceled_email_success(self, mock_send_email, faker: Faker):
        """Test successful registration canceled email sending."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="Mónica",
            last_name="Herrera",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )
        event = self.create_test_event(faker)
        event.name = "Taller de Diseño UX"

        # Act
        send_registration_canceled_email(user, event)

        # Assert
        mock_send_email.assert_called_once_with(
            user,
            "Cancelaste el evento 'Taller de Diseño UX' en la UDLA",
            "registration_canceled.html",
            {
                "first_name": "Mónica",
                "event_name": "Taller de Diseño UX",
            }
        )

    @patch('app.helpers.mail._send_email')
    def test_send_registration_canceled_email_with_special_event_name(self, mock_send_email, faker: Faker):
        """Test registration canceled email with special characters in event name."""
        # Arrange
        user = User(
            id=1,
            email=faker.email(),
            first_name="Alejandro",
            last_name="Ruiz",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )
        event = self.create_test_event(faker)
        event.name = "Conferencia: AI & Machine Learning 2025"

        # Act
        send_registration_canceled_email(user, event)

        # Assert
        mock_send_email.assert_called_once_with(
            user,
            "Cancelaste el evento 'Conferencia: AI & Machine Learning 2025' en la UDLA",
            "registration_canceled.html",
            {
                "first_name": "Alejandro",
                "event_name": "Conferencia: AI & Machine Learning 2025",
            }
        )


class TestEmailIntegration:
    """Integration tests for email functionality."""

    @patch('app.helpers.mail.connect_to_smtp_server')
    @patch('app.helpers.mail.templates')
    @patch('app.helpers.mail.settings')
    def test_email_message_construction(self, mock_settings, mock_templates, mock_connect, faker: Faker):
        """Test that EmailMessage is constructed correctly."""
        # Arrange
        mock_settings.EMAIL_SENDER = "noreply@udla.edu.ec"
        user = User(
            id=1,
            email="test@udla.edu.ec",
            first_name="Test",
            last_name="User",
            hashed_password=b"hashed_password",
            role=Role.ASSISTANT
        )
        
        mock_template = Mock()
        mock_template.render.return_value = "<html><body>Test Email</body></html>"
        mock_templates.get_template.return_value = mock_template
        
        mock_server = Mock()
        mock_connect.return_value.__enter__.return_value = mock_server

        # Act
        _send_email(user, "Test Subject", "test.html", {"key": "value"})

        # Assert
        mock_server.sendmail.assert_called_once()
        call_args = mock_server.sendmail.call_args[0]
        
        # Verify sender and recipient
        assert call_args[0] == "noreply@udla.edu.ec"
        assert call_args[1] == "test@udla.edu.ec"
        
        # Verify email content contains HTML
        email_content = call_args[2]
        assert "Test Subject" in email_content
        assert "Test Email" in email_content