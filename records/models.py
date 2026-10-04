from django.conf import settings
from django.db import models

from config.fields import EncryptedTextField


class MedicalRecord(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="records")
    doctor = models.ForeignKey("accounts.DoctorProfile", on_delete=models.SET_NULL, null=True, related_name="records")
    appointment = models.ForeignKey("appointments.Appointment", on_delete=models.SET_NULL, null=True, blank=True)
    diagnosis = EncryptedTextField()
    treatment = EncryptedTextField(blank=True)
    notes = EncryptedTextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Record {self.pk} for {self.patient}"


class TestResult(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="test_results")
    ordered_by = models.ForeignKey("accounts.DoctorProfile", on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=120)
    result = EncryptedTextField()
    reference_range = models.CharField(max_length=120, blank=True)
    report_file = models.FileField(upload_to="test_reports/", blank=True)
    test_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-test_date"]

    def __str__(self):
        return f"{self.name} ({self.patient})"
