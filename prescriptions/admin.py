from django.contrib import admin

from .models import Pharmacy, PharmacyOrder, Prescription, PrescriptionItem


class ItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 0


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "created_at", "refill_date")
    inlines = [ItemInline]


@admin.register(PharmacyOrder)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "prescription", "pharmacy", "status", "created_at")
    list_filter = ("status", "pharmacy")
    list_editable = ("status",)


admin.site.register(Pharmacy)
