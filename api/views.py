from datetime import date

from django.db.models import Q
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import DoctorProfile
from appointments.models import Appointment
from appointments.services import available_slots
from notifications.models import Notification
from notifications.services import notify
from payments.models import Payment
from prescriptions.models import Prescription
from records.models import MedicalRecord, TestResult

from .permissions import IsDoctor, IsPatient
from .serializers import (AppointmentSerializer, DoctorSerializer, MedicalRecordSerializer,
                          NotificationSerializer, PaymentSerializer, PrescriptionSerializer,
                          RegisterSerializer, TestResultSerializer)


def doctor_patient_ids(user):
    return Appointment.objects.filter(doctor__user=user).values_list("patient_id", flat=True)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DoctorSerializer

    def get_queryset(self):
        qs = DoctorProfile.objects.filter(is_approved=True).select_related("user")
        spec = self.request.query_params.get("specialization")
        return qs.filter(specialization__icontains=spec) if spec else qs

    @action(detail=True, methods=["get"])
    def slots(self, request, pk=None):
        try:
            day = date.fromisoformat(request.query_params.get("date", ""))
        except ValueError:
            return Response({"detail": "Provide ?date=YYYY-MM-DD"}, status=400)
        return Response({"date": day, "slots": [t.strftime("%H:%M") for t in available_slots(self.get_object(), day)]})


class AppointmentViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = AppointmentSerializer

    def get_permissions(self):
        return [IsPatient()] if self.action == "create" else super().get_permissions()

    def get_queryset(self):
        u = self.request.user
        qs = Appointment.objects.select_related("doctor__user", "patient")
        if u.is_patient:
            return qs.filter(patient=u)
        if u.is_doctor:
            return qs.filter(doctor__user=u)
        return qs if u.is_admin_role else qs.none()

    def perform_create(self, serializer):
        appt = serializer.save(patient=self.request.user)
        notify(appt.doctor.user, "New appointment request", f"{self.request.user.display_name}: {appt.date} {appt.time:%H:%M}")

    def _transition(self, request, new, allowed_from, doctor_only=False):
        appt = self.get_object()
        if doctor_only and not request.user.is_doctor:
            return Response(status=403)
        if appt.status not in allowed_from:
            return Response({"detail": f"Cannot {new} from {appt.status}."}, status=400)
        appt.status = new
        appt.save(update_fields=["status"])
        return Response(self.get_serializer(appt).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._transition(request, "confirmed", ["pending"], doctor_only=True)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        return self._transition(request, "completed", ["confirmed"], doctor_only=True)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(request, "cancelled", ["pending", "confirmed"])


class MedicalRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MedicalRecordSerializer

    def get_queryset(self):
        u = self.request.user
        if u.is_patient:
            return MedicalRecord.objects.filter(patient=u)
        if u.is_doctor:
            return MedicalRecord.objects.filter(patient_id__in=doctor_patient_ids(u))
        return MedicalRecord.objects.all() if u.is_admin_role else MedicalRecord.objects.none()


class TestResultViewSet(MedicalRecordViewSet):
    serializer_class = TestResultSerializer

    def get_queryset(self):
        u = self.request.user
        if u.is_patient:
            return TestResult.objects.filter(patient=u)
        if u.is_doctor:
            return TestResult.objects.filter(patient_id__in=doctor_patient_ids(u))
        return TestResult.objects.all() if u.is_admin_role else TestResult.objects.none()


class PrescriptionViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = PrescriptionSerializer

    def get_permissions(self):
        return [IsDoctor()] if self.action == "create" else super().get_permissions()

    def get_queryset(self):
        u = self.request.user
        qs = Prescription.objects.prefetch_related("items")
        if u.is_patient:
            return qs.filter(patient=u)
        if u.is_doctor:
            return qs.filter(doctor__user=u)
        return qs if u.is_admin_role else qs.none()

    def perform_create(self, serializer):
        patient = serializer.validated_data["patient"]
        if patient.pk not in set(doctor_patient_ids(self.request.user)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only prescribe to your own patients.")
        rx = serializer.save()
        notify(patient, "New prescription", "A new prescription was issued.", kind="prescription")


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        u = self.request.user
        if u.is_patient:
            return Payment.objects.filter(user=u)
        if u.is_doctor:
            return Payment.objects.filter(appointment__doctor__user=u)
        return Payment.objects.all() if u.is_admin_role else Payment.objects.none()


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        self.get_queryset().update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
