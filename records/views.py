from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import can_access_patient, role_required
from accounts.models import DoctorProfile
from appointments.models import Appointment
from notifications.services import notify

from .forms import MedicalRecordForm, TestResultForm
from .models import MedicalRecord, TestResult

User = get_user_model()


@role_required("patient", "doctor", "staff", "admin")
def history(request, patient_id=None):
    patient = request.user if (patient_id is None and request.user.is_patient) else get_object_or_404(
        User, pk=patient_id, role="patient")
    if not can_access_patient(request.user, patient):
        raise PermissionDenied
    return render(request, "records/history.html", {
        "patient": patient,
        "profile": getattr(patient, "patient_profile", None),
        "records": patient.records.select_related("doctor__user"),
        "tests": patient.test_results.all(),
    })


@role_required("doctor")
def my_patients(request):
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    ids = Appointment.objects.filter(doctor=doctor).values_list("patient", flat=True).distinct()
    return render(request, "records/patients.html", {"patients": User.objects.filter(pk__in=ids)})


@role_required("doctor")
def add_record(request, appointment_id):
    appt = get_object_or_404(Appointment, pk=appointment_id, doctor__user=request.user)
    form = MedicalRecordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        rec = form.save(commit=False)
        rec.patient, rec.doctor, rec.appointment = appt.patient, appt.doctor, appt
        rec.save()
        messages.success(request, "Medical record saved.")
        return redirect("records:patient", patient_id=appt.patient_id)
    return render(request, "form.html", {"form": form, "title": f"Medical record - {appt.patient.display_name}",
                                         "submit": "Save record"})


@role_required("doctor")
def add_test(request, patient_id):
    patient = get_object_or_404(User, pk=patient_id, role="patient")
    if not can_access_patient(request.user, patient):
        raise PermissionDenied
    form = TestResultForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        t = form.save(commit=False)
        t.patient, t.ordered_by = patient, request.user.doctor_profile
        t.save()
        notify(patient, "Test result available", f"Your {t.name} result is ready.", kind="test",
               link="/records/", send_sms=True)
        messages.success(request, "Test result added; patient notified.")
        return redirect("records:patient", patient_id=patient.pk)
    return render(request, "form.html", {"form": form, "title": f"Add test result - {patient.display_name}",
                                         "submit": "Save", "multipart": True})
