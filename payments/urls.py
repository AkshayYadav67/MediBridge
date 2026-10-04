from django.urls import path

from . import views

app_name = "payments"
urlpatterns = [
    path("", views.history, name="history"),
    path("appointment/<int:appointment_id>/", views.pay_appointment, name="pay_appointment"),
    path("<int:pk>/pay/", views.pay, name="pay"),
    path("<int:pk>/dispute/", views.raise_dispute, name="dispute"),
    path("charge/<int:patient_id>/", views.create_charge, name="charge"),
]
