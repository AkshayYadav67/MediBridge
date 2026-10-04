from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import DoctorAvailability, DoctorProfile, PatientProfile, User
from appointments.models import Appointment
from appointments.services import available_slots
from payments.gateway import MockGateway
from records.models import MedicalRecord


def next_weekday(wd):
    d = timezone.localdate() + timedelta(days=1)
    while d.weekday() != wd:
        d += timedelta(days=1)
    return d


class Base(TestCase):
    def setUp(self):
        self.pu = User.objects.create_user("pat", password="x12345678!", role="patient", email="p@x.com")
        PatientProfile.objects.create(user=self.pu)
        self.du = User.objects.create_user("doc", password="x12345678!", role="doctor", email="d@x.com")
        self.doc = DoctorProfile.objects.create(user=self.du, specialization="Derm", is_approved=True)
        DoctorAvailability.objects.create(doctor=self.doc, weekday=0, start_time=time(9), end_time=time(11))
        self.day = next_weekday(0)


class SlotTests(Base):
    def test_slots_and_booking_removes_slot(self):
        self.assertEqual(len(available_slots(self.doc, self.day)), 4)
        Appointment.objects.create(patient=self.pu, doctor=self.doc, date=self.day, time=time(9), reason="x")
        self.assertNotIn(time(9), available_slots(self.doc, self.day))

    def test_cancelled_slot_is_free_again(self):
        a = Appointment.objects.create(patient=self.pu, doctor=self.doc, date=self.day, time=time(9), reason="x")
        a.status = "cancelled"; a.save()
        self.assertIn(time(9), available_slots(self.doc, self.day))


class FlowTests(Base):
    def test_full_flow(self):
        self.client.login(username="pat", password="x12345678!")
        r = self.client.post(reverse("appointments:book", args=[self.doc.pk]), {
            "date": self.day.isoformat(), "time": "09:30", "mode": "video", "reason": "rash"})
        self.assertEqual(r.status_code, 302)
        appt = Appointment.objects.get()
        self.client.logout()
        self.client.login(username="doc", password="x12345678!")
        self.client.post(reverse("appointments:status", args=[appt.pk, "confirm"]))
        appt.refresh_from_db()
        self.assertEqual(appt.status, "confirmed")
        r = self.client.post(reverse("records:add", args=[appt.pk]), {"diagnosis": "Eczema", "treatment": "Cream", "notes": ""})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(MedicalRecord.objects.get().diagnosis, "Eczema")

    def test_patient_cannot_see_other_patient_records(self):
        other = User.objects.create_user("p2", password="x12345678!", role="patient")
        self.client.login(username="pat", password="x12345678!")
        self.assertEqual(self.client.get(reverse("records:patient", args=[other.pk])).status_code, 403)

    def test_patient_cannot_open_reports(self):
        self.client.login(username="pat", password="x12345678!")
        self.assertEqual(self.client.get(reverse("reports:dashboard")).status_code, 403)

    def test_payment_gateway(self):
        self.assertTrue(MockGateway().charge(10, "4242 4242 4242 4242").success)
        self.assertFalse(MockGateway().charge(10, "4000 0000 0000 0002").success)

    def test_record_encrypted_at_rest(self):
        from django.db import connection
        MedicalRecord.objects.create(patient=self.pu, doctor=self.doc, diagnosis="SECRET-DX")
        with connection.cursor() as c:
            c.execute("SELECT diagnosis FROM records_medicalrecord")
            self.assertNotIn("SECRET-DX", c.fetchone()[0])


class ApiTests(Base):
    def test_jwt_and_booking(self):
        r = self.client.post("/api/auth/token/", {"username": "pat", "password": "x12345678!"})
        tok = r.json()["access"]
        h = {"HTTP_AUTHORIZATION": f"Bearer {tok}"}
        self.assertEqual(self.client.get("/api/doctors/", **h).status_code, 200)
        r = self.client.post("/api/appointments/", {"doctor": self.doc.pk, "date": self.day.isoformat(), "time": "10:00",
                                                    "mode": "video", "reason": "check"}, content_type="application/json", **h)
        self.assertEqual(r.status_code, 201, r.content)
        r = self.client.post("/api/appointments/", {"doctor": self.doc.pk, "date": self.day.isoformat(), "time": "10:00",
                                                    "mode": "video", "reason": "again"}, content_type="application/json", **h)
        self.assertEqual(r.status_code, 400)

    def test_api_requires_auth(self):
        self.assertEqual(self.client.get("/api/appointments/").status_code, 401)
