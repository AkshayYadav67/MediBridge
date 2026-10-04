from datetime import date

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import DoctorProfile
from notifications.services import notify

from .forms import BookingForm, FeedbackForm
from .models import Appointment
from .services import available_slots


@role_required("patient")
def book(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, pk=doctor_id, is_approved=True)
    raw = request.POST.get("date") or request.GET.get("date")
    day = None
    try:
        day = date.fromisoformat(raw) if raw else None
    except ValueError:
        messages.error(request, "Invalid date.")
    slots = available_slots(doctor, day) if day and day >= timezone.localdate() else []
    form = BookingForm(request.POST or None, slots=slots, initial={"date": day})
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                appt = Appointment.objects.create(
                    patient=request.user, doctor=doctor, date=form.cleaned_data["date"],
                    time=form.cleaned_data["time"], mode=form.cleaned_data["mode"],
                    reason=form.cleaned_data["reason"])
        except IntegrityError:
            messages.error(request, "Sorry, that slot was just taken. Please pick another.")
            return redirect(f"{request.path}?date={day}")
        notify(doctor.user, "New appointment request",
               f"{request.user.display_name} requested {appt.date} at {appt.time:%H:%M}.", kind="appointment")
        notify(request.user, "Appointment requested",
               f"Your request with {doctor} on {appt.date} at {appt.time:%H:%M} is awaiting confirmation.",
               kind="appointment")
        messages.success(request, "Appointment requested.")
        return redirect("appointments:detail", pk=appt.pk)
    return render(request, "appointments/book.html", {"doctor": doctor, "day": day, "slots": slots, "form": form,
                                                       "today": timezone.localdate()})


def _visible(user):
    qs = Appointment.objects.select_related("doctor__user", "patient")
    if user.is_patient:
        return qs.filter(patient=user)
    if user.is_doctor:
        return qs.filter(doctor__user=user)
    return qs


@role_required("patient", "doctor", "staff", "admin")
def appointment_list(request):
    qs = _visible(request.user)
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    return render(request, "appointments/list.html", {"appointments": qs, "status": status,
                                                       "statuses": Appointment.Status.choices})


@role_required("patient", "doctor", "staff", "admin")
def detail(request, pk):
    appt = get_object_or_404(_visible(request.user), pk=pk)
    return render(request, "appointments/detail.html", {
        "appt": appt, "feedback": getattr(appt, "feedback", None),
        "records": appt.medicalrecord_set.all(), "prescriptions": appt.prescription_set.all()})


@require_POST
@role_required("patient", "doctor")
def change_status(request, pk, action):
    appt = get_object_or_404(_visible(request.user), pk=pk)
    user = request.user
    allowed = {
        "confirm": (user.is_doctor and appt.status == "pending", "confirmed"),
        "complete": (user.is_doctor and appt.status == "confirmed", "completed"),
        "cancel": (appt.is_open, "cancelled"),
    }
    ok, new_status = allowed.get(action, (False, None))
    if not ok:
        messages.error(request, "That action isn't available.")
        return redirect("appointments:detail", pk=pk)
    appt.status = new_status
    appt.save(update_fields=["status"])
    other = appt.patient if user.is_doctor else appt.doctor.user
    notify(other, f"Appointment {new_status}",
           f"Appointment on {appt.date} at {appt.time:%H:%M} is now {new_status}.", kind="appointment", send_sms=True)
    messages.success(request, f"Appointment {new_status}.")
    return redirect("appointments:detail", pk=pk)


@role_required("patient")
def leave_feedback(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, patient=request.user, status="completed")
    if hasattr(appt, "feedback"):
        messages.info(request, "Feedback already submitted.")
        return redirect("appointments:detail", pk=pk)
    form = FeedbackForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        fb = form.save(commit=False)
        fb.appointment = appt
        fb.save()
        messages.success(request, "Thanks for your feedback!")
        return redirect("appointments:detail", pk=pk)
    return render(request, "form.html", {"form": form, "title": "Rate your consultation", "submit": "Submit"})
