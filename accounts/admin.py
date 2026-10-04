from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import DoctorAvailability, DoctorProfile, PatientProfile, User


@admin.register(User)
class MediUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_active")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (("MediBridge", {"fields": ("role", "phone")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("MediBridge", {"fields": ("role", "phone", "email")}),)


class AvailabilityInline(admin.TabularInline):
    model = DoctorAvailability
    extra = 0


@admin.register(DoctorProfile)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("user", "specialization", "consultation_fee", "is_approved")
    list_filter = ("is_approved", "specialization")
    actions = ["approve"]
    inlines = [AvailabilityInline]

    @admin.action(description="Approve selected doctors")
    def approve(self, request, queryset):
        queryset.update(is_approved=True)


admin.site.register(PatientProfile)
