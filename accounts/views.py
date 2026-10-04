from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from appointments.models import Appointment
from prescriptions.models import Prescription

from .decorators import role_required
from .forms import (AvailabilityForm, DoctorProfileForm, PatientProfileForm,
                    RegistrationForm, UserForm)
from .models import DoctorAvailability, DoctorProfile, PatientProfile


def home(request):
    doctors = DoctorProfile.objects.filter(is_approved=True).select_related("user")[:6]
    return render(request, "home.html", {"doctors": doctors})


def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        if user.is_doctor:
            messages.info(request, "Account created. An administrator must approve your profile before patients can book you.")
        else:
            messages.success(request, "Welcome to MediBridge!")
        return redirect("accounts:dashboard")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    user, today = request.user, timezone.localdate()
    if user.is_patient:
        return render(request, "accounts/dashboard_patient.html", {
            "upcoming": Appointment.objects.filter(patient=user, date__gte=today)
                .exclude(status__in=["cancelled", "completed"]).select_related("doctor__user")[:5],
            "prescriptions": Prescription.objects.filter(patient=user).select_related("doctor__user")[:5],
        })
    if user.is_doctor:
        profile = get_object_or_404(DoctorProfile, user=user)
        qs = Appointment.objects.filter(doctor=profile).select_related("patient")
        return render(request, "accounts/dashboard_doctor.html", {
            "profile": profile,
            "today": qs.filter(date=today).exclude(status="cancelled"),
            "pending": qs.filter(status="pending"),
        })
    return redirect("reports:dashboard")


@login_required
def profile(request):
    user = request.user
    profile_form = None
    if user.is_patient:
        obj, _ = PatientProfile.objects.get_or_create(user=user)
        profile_form = PatientProfileForm(request.POST or None, instance=obj)
    elif user.is_doctor:
        profile_form = DoctorProfileForm(request.POST or None, instance=get_object_or_404(DoctorProfile, user=user))
    user_form = UserForm(request.POST or None, instance=user)
    if request.method == "POST" and user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
        user_form.save()
        if profile_form:
            profile_form.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"user_form": user_form, "profile_form": profile_form})


@role_required("doctor")
def availability(request):
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    form = AvailabilityForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        slot = form.save(commit=False)
        slot.doctor = doctor
        slot.save()
        messages.success(request, "Availability added.")
        return redirect("accounts:availability")
    return render(request, "accounts/availability.html", {"form": form, "slots": doctor.availability.all()})


@role_required("doctor")
def availability_delete(request, pk):
    slot = get_object_or_404(DoctorAvailability, pk=pk, doctor__user=request.user)
    if request.method == "POST":
        slot.delete()
    return redirect("accounts:availability")


def doctor_list(request):
    qs = DoctorProfile.objects.filter(is_approved=True).select_related("user")
    spec = request.GET.get("specialization", "").strip()
    if spec:
        qs = qs.filter(specialization__icontains=spec)
    return render(request, "accounts/doctor_list.html", {"doctors": qs, "spec": spec})
