from django.urls import path

from . import views

app_name = "reports"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.user_list, name="users"),
    path("users/<int:pk>/toggle/", views.toggle_user, name="toggle_user"),
    path("doctors/<int:pk>/approve/", views.approve_doctor, name="approve_doctor"),
    path("disputes/", views.disputes, name="disputes"),
    path("disputes/<int:pk>/resolve/", views.resolve_dispute, name="resolve_dispute"),
    path("export/<str:kind>.csv", views.export_csv, name="export"),
]
