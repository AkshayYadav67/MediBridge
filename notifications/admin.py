from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "kind", "is_read", "email_sent", "sms_sent", "created_at")
    list_filter = ("kind", "is_read")
