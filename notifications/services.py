import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils.module_loading import import_string

from .models import Notification

log = logging.getLogger(__name__)


def notify(user, title, message, kind="info", link="", send_email=True, send_sms=False):
    """Create an in-app notification and optionally deliver by email / SMS. Never raises."""
    n = Notification.objects.create(user=user, title=title, message=message, kind=kind, link=link)
    if send_email and user.email:
        try:
            send_mail(f"[MediBridge] {title}", message, settings.DEFAULT_FROM_EMAIL, [user.email])
            n.email_sent = True
        except Exception:
            log.exception("email failed")
    if send_sms and getattr(user, "phone", ""):
        try:
            n.sms_sent = import_string(settings.SMS_BACKEND)().send(user.phone, f"MediBridge: {message}")
        except Exception:
            log.exception("sms failed")
    n.save(update_fields=["email_sent", "sms_sent"])
    return n
