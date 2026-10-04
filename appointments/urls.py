from django.urls import path

from . import views

app_name = "appointments"
urlpatterns = [
    path("", views.appointment_list, name="list"),
    path("book/<int:doctor_id>/", views.book, name="book"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/<str:action>/", views.change_status, name="status"),
    path("<int:pk>/feedback/new/", views.leave_feedback, name="feedback"),
]
