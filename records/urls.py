from django.urls import path

from . import views

app_name = "records"
urlpatterns = [
    path("", views.history, name="mine"),
    path("patients/", views.my_patients, name="patients"),
    path("patient/<int:patient_id>/", views.history, name="patient"),
    path("appointment/<int:appointment_id>/add/", views.add_record, name="add"),
    path("patient/<int:patient_id>/test/add/", views.add_test, name="add_test"),
]
