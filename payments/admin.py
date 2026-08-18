from django.contrib import admin

from payments.models import DailyPayment, PaymentHead


@admin.register(PaymentHead)
class PaymentHeadAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "description", "is_active")
    search_fields = ("code", "description")


@admin.register(DailyPayment)
class DailyPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "business_date",
        "institution",
        "payment_head",
        "amount",
        "entered_by",
        "is_active",
    )
    list_filter = ("is_active", "institution", "business_date")
