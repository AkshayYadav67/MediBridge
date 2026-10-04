"""Payment gateway abstraction. Swap MockGateway for Stripe/Khalti/eSewa by writing another class with
`charge()` and `refund()` and pointing the PAYMENT_GATEWAY setting at it."""
import uuid
from dataclasses import dataclass

from django.conf import settings
from django.utils.module_loading import import_string


@dataclass
class ChargeResult:
    success: bool
    transaction_id: str = ""
    error: str = ""


class MockGateway:
    """Demo gateway. Card numbers ending in 0002 are declined; everything else succeeds.
    NEVER store card numbers - only the last 4 digits are used here and nothing is persisted."""

    def charge(self, amount, card_number, **kw):
        digits = "".join(c for c in card_number if c.isdigit())
        if len(digits) < 12:
            return ChargeResult(False, error="Invalid card number.")
        if digits.endswith("0002"):
            return ChargeResult(False, error="Card declined.")
        return ChargeResult(True, transaction_id=f"MOCK-{uuid.uuid4().hex[:12].upper()}")

    def refund(self, transaction_id):
        return True


def get_gateway():
    return import_string(settings.PAYMENT_GATEWAY)()
