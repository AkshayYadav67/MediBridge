from django.contrib import admin

from .models import Appointment, Feedback


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "date", "time", "mode", "status")
    list_filter = ("status", "mode", "date")
    search_fields = ("patient__username", "doctor__user__username")


admin.site.register(Feedback)
