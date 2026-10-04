from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register("doctors", views.DoctorViewSet, basename="api-doctor")
router.register("appointments", views.AppointmentViewSet, basename="api-appointment")
router.register("records", views.MedicalRecordViewSet, basename="api-record")
router.register("tests", views.TestResultViewSet, basename="api-test")
router.register("prescriptions", views.PrescriptionViewSet, basename="api-prescription")
router.register("payments", views.PaymentViewSet, basename="api-payment")
router.register("notifications", views.NotificationViewSet, basename="api-notification")

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("", include(router.urls)),
]
