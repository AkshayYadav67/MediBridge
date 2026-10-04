"""Run daily (cron / Celery beat / docker scheduler):  python manage.py send_reminders"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from appointments.models import Appointment
from notifications.services import notify
from prescriptions.models import Prescription


class Command(BaseCommand):
    help = "Send appointment reminders (next 24h) and prescription refill alerts."

    def handle(self, *args, **opts):
        today = timezone.localdate()
        count = 0
        for a in Appointment.objects.filter(status="confirmed", reminder_sent=False,
                                            date__in=[today, today + timedelta(days=1)]):
            notify(a.patient, "Appointment reminder",
                   f"Reminder: {a.doctor} on {a.date} at {a.time:%H:%M} ({a.get_mode_display()}).",
                   kind="reminder", link=f"/appointments/{a.pk}/", send_sms=True)
            a.reminder_sent = True
            a.save(update_fields=["reminder_sent"])
            count += 1
        for p in Prescription.objects.filter(refill_date__lte=today + timedelta(days=2), refill_notified=False):
            notify(p.patient, "Prescription refill due",
                   f"Your prescription from {p.doctor} is due for refill on {p.refill_date}.",
                   kind="reminder", link=f"/prescriptions/{p.pk}/", send_sms=True)
            p.refill_notified = True
            p.save(update_fields=["refill_notified"])
            count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} reminders sent"))
