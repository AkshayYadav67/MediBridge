"""Pluggable SMS backends. Select with the SMS_BACKEND setting."""
import logging

from django.conf import settings

log = logging.getLogger(__name__)


class ConsoleSMSBackend:
    def send(self, to, body):
        log.info("[SMS to %s] %s", to, body)
        print(f"[SMS to {to}] {body}")
        return True


class TwilioSMSBackend:
    def send(self, to, body):
        from twilio.rest import Client  # pip install twilio
        Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN).messages.create(
            to=to, from_=settings.TWILIO_FROM_NUMBER, body=body)
        return True
