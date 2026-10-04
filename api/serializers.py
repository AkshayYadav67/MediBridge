from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import DoctorProfile, PatientProfile
from appointments.models import Appointment
from appointments.services import available_slots
from notifications.models import Notification
from payments.models import Payment
from prescriptions.models import Prescription, PrescriptionItem
from records.models import MedicalRecord, TestResult

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["patient", "doctor"], default="patient")
    specialization = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = ("username", "password", "email", "first_name", "last_name", "phone", "role", "specialization")

    def validate(self, data):
        validate_password(data["password"])
        if data["role"] == "doctor" and not data.get("specialization"):
            raise serializers.ValidationError({"specialization": "Required for doctors."})
        return data

    def create(self, validated):
        spec = validated.pop("specialization", "")
        pw = validated.pop("password")
        user = User(**validated)
        user.set_password(pw)
        user.save()
        if user.role == "doctor":
            DoctorProfile.objects.create(user=user, specialization=spec)
        else:
            PatientProfile.objects.create(user=user)
        return user


class DoctorSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ("id", "name", "specialization", "experience_years", "consultation_fee", "bio")


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.user.display_name", read_only=True)
    patient_name = serializers.CharField(source="patient.display_name", read_only=True)
    is_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = ("id", "doctor", "doctor_name", "patient_name", "date", "time", "mode", "reason", "status", "is_paid")
        read_only_fields = ("status",)

    def validate(self, data):
        if data["doctor"].is_approved is False:
            raise serializers.ValidationError("Doctor is not available for booking.")
        if data["time"] not in available_slots(data["doctor"], data["date"]):
            raise serializers.ValidationError("That time slot is not available.")
        return data


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ("id", "patient", "doctor", "appointment", "diagnosis", "treatment", "notes", "created_at")


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = ("id", "patient", "name", "result", "reference_range", "test_date")


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = ("medicine", "dosage", "frequency", "duration_days", "instructions")


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True)

    class Meta:
        model = Prescription
        fields = ("id", "patient", "appointment", "diagnosis", "notes", "refill_date", "items", "created_at")
        read_only_fields = ("created_at",)

    def create(self, validated):
        items = validated.pop("items")
        rx = Prescription.objects.create(doctor=self.context["request"].user.doctor_profile, **validated)
        PrescriptionItem.objects.bulk_create([PrescriptionItem(prescription=rx, **i) for i in items])
        return rx


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "appointment", "purpose", "description", "amount", "status", "transaction_id", "created_at")


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "title", "message", "kind", "link", "is_read", "created_at")
