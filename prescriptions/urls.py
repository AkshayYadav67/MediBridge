from django.urls import path

from . import views

app_name = "prescriptions"
urlpatterns = [
    path("", views.prescription_list, name="list"),
    path("<int:pk>/", views.prescription_detail, name="detail"),
    path("appointment/<int:appointment_id>/new/", views.prescription_create, name="create"),
    path("<int:pk>/order/", views.order_pharmacy, name="order"),
]
