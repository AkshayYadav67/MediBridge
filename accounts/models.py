from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        DOCTOR = "doctor", "Doctor"
        STAFF = "staff", "Staff"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PATIENT)
    phone = models.CharField(max_length=20, blank=True)

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_admin_role(self):
        return self.role in (self.Role.ADMIN, self.Role.STAFF)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        if self.role in (self.Role.ADMIN, self.Role.STAFF):
            self.is_staff = True
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.get_full_name() or self.username


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, choices=[("M", "Male"), ("F", "Female"), ("O", "Other")])
    blood_group = models.CharField(max_length=3, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=120, blank=True)
    allergies = models.TextField(blank=True)

    def __str__(self):
        return f"Patient: {self.user.display_name}"


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500)
    bio = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False, help_text="Only approved doctors can be booked.")

    class Meta:
        ordering = ["user__first_name"]

    def __str__(self):
        return f"Dr. {self.user.display_name} ({self.specialization})"


class DoctorAvailability(models.Model):
    WEEKDAYS = [(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
                (4, "Friday"), (5, "Saturday"), (6, "Sunday")]
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="availability")
    weekday = models.IntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_minutes = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ["weekday", "start_time"]
        verbose_name_plural = "doctor availability"

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"
