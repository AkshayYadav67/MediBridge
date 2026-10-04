import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Mode(models.TextChoices):
        IN_PERSON = "in_person", "In person"
        VIDEO = "video", "Video consultation"

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey("accounts.DoctorProfile", on_delete=models.CASCADE, related_name="appointments")
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField()
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.VIDEO)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    room_id = models.UUIDField(default=uuid.uuid4, editable=False)
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-time"]
        constraints = [models.UniqueConstraint(
            fields=["doctor", "date", "time"], condition=~Q(status="cancelled"), name="unique_active_slot")]

    def __str__(self):
        return f"{self.patient} -> {self.doctor} on {self.date} {self.time:%H:%M}"

    @property
    def fee(self):
        return self.doctor.consultation_fee

    @property
    def is_paid(self):
        return self.payments.filter(status="paid").exists()

    @property
    def is_open(self):
        return self.status in (self.Status.PENDING, self.Status.CONFIRMED)


class Feedback(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} ★") for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating}★ for {self.appointment}"
