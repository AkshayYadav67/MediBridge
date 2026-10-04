from django.urls import path

from . import views

app_name = "telemedicine"
urlpatterns = [
    path("<int:pk>/", views.room, name="room"),
    path("<int:pk>/messages/", views.messages_json, name="messages"),
    path("<int:pk>/send/", views.send_message, name="send"),
]
