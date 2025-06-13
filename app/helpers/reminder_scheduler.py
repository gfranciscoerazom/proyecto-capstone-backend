# reminder_scheduler.py
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlmodel import Session, select
from app.db.database import get_engine, Event, Registration, User
from app.helpers.mail import send_event_reminder_email

def send_reminders():
    engine = get_engine()
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
    with Session(engine) as session:
        events = session.exec(
            select(Event).where(Event.date == tomorrow)
        ).all()
        for event in events:
            registrations = session.exec(
                select(Registration).where(Registration.event_id == event.id)
            ).all()
            for reg in registrations:
                user = session.get(User, reg.assistant_id)
                if user:
                    send_event_reminder_email(user, event)

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(send_reminders, 'cron', hour=8)  # Every day at 8am
    scheduler.start()