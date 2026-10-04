"""EncryptedTextField: Fernet (AES-128-CBC + HMAC) encryption of sensitive text at rest."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _fernet():
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.FIELD_ENCRYPTION_KEY.encode()).digest())
    return Fernet(key)


class EncryptedTextField(models.TextField):
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value:
            return value
        return _fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return value  # legacy plaintext
