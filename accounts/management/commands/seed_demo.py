"""python manage.py seed_demo  -> demo admin, doctors, patient, pharmacy (password: demo12345)."""
from datetime import time

from django.core.management.base import BaseCommand

from accounts.models import DoctorAvailability, DoctorProfile, PatientProfile, User
from prescriptions.models import Pharmacy


class Command(BaseCommand):
    help = "Create demo data"

    def handle(self, *args, **opts):
        pw = "demo12345"
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@medibridge.local", pw)
        specs = [("drsharma", "Dermatology", 800), ("drkarki", "Cardiology", 1200), ("drthapa", "General Medicine", 500)]
        for username, spec, fee in specs:
            u, created = User.objects.get_or_create(username=username, defaults={
                "role": "doctor", "first_name": username[2:].title(), "last_name": "MD",
                "email": f"{username}@medibridge.local"})
            if created:
                u.set_password(pw); u.save()
                d = DoctorProfile.objects.create(user=u, specialization=spec, consultation_fee=fee,
                                                 experience_years=8, is_approved=True, bio=f"{spec} specialist.")
                for wd in range(0, 5):
                    DoctorAvailability.objects.create(doctor=d, weekday=wd, start_time=time(9), end_time=time(16))
        p, created = User.objects.get_or_create(username="patient1", defaults={
            "role": "patient", "first_name": "Asha", "last_name": "Rai", "email": "asha@medibridge.local",
            "phone": "+9779800000000"})
        if created:
            p.set_password(pw); p.save()
            PatientProfile.objects.create(user=p)
        Pharmacy.objects.get_or_create(name="CityCare Pharmacy", defaults={
            "address": "Main Road, Dharan", "phone": "025-000000", "email": "citycare@example.com"})
        self.stdout.write(self.style.SUCCESS("Demo data ready. Logins: admin / drsharma / patient1  (password demo12345)"))
