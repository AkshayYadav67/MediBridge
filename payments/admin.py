from django.contrib import admin

from .models import Dispute, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "purpose", "amount", "status", "transaction_id", "created_at")
    list_filter = ("status", "purpose")


admin.site.register(Dispute)
