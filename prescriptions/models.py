from django.conf import settings
from django.db import models


class Prescription(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prescriptions")
    doctor = models.ForeignKey("accounts.DoctorProfile", on_delete=models.SET_NULL, null=True, related_name="prescriptions")
    appointment = models.ForeignKey("appointments.Appointment", on_delete=models.SET_NULL, null=True, blank=True)
    diagnosis = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    refill_date = models.DateField(null=True, blank=True)
    refill_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Rx #{self.pk} for {self.patient}"


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="items")
    medicine = models.CharField(max_length=120)
    dosage = models.CharField(max_length=60, help_text="e.g. 500 mg")
    frequency = models.CharField(max_length=60, help_text="e.g. twice daily")
    duration_days = models.PositiveIntegerField(default=5)
    instructions = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.medicine} {self.dosage}"


class Pharmacy(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "pharmacies"

    def __str__(self):
        return self.name


class PharmacyOrder(models.Model):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        PREPARING = "preparing", "Preparing"
        OUT = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="orders")
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.PROTECT)
    delivery_address = models.TextField()
    contact_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLACED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
