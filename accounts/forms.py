from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import DoctorAvailability, DoctorProfile, PatientProfile, User


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=[("patient", "Patient"), ("doctor", "Doctor")], initial="patient")
    specialization = forms.CharField(required=False, help_text="Doctors only")
    license_number = forms.CharField(required=False, help_text="Doctors only")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "role")

    def clean(self):
        data = super().clean()
        if data.get("role") == "doctor" and not data.get("specialization"):
            self.add_error("specialization", "Specialization is required for doctors.")
        if not data.get("email"):
            self.add_error("email", "Email is required for reminders.")
        return data

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            if user.role == "doctor":
                DoctorProfile.objects.create(
                    user=user,
                    specialization=self.cleaned_data["specialization"],
                    license_number=self.cleaned_data.get("license_number", ""),
                )
            else:
                PatientProfile.objects.create(user=user)
        return user


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        exclude = ("user",)
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ("specialization", "license_number", "experience_years", "consultation_fee", "bio")


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = DoctorAvailability
        fields = ("weekday", "start_time", "end_time", "slot_minutes")
        widgets = {"start_time": forms.TimeInput(attrs={"type": "time"}),
                   "end_time": forms.TimeInput(attrs={"type": "time"})}

    def clean(self):
        d = super().clean()
        if d.get("start_time") and d.get("end_time") and d["start_time"] >= d["end_time"]:
            raise forms.ValidationError("End time must be after start time.")
        return d
