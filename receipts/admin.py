from django.contrib import admin

from receipts.models import DailyReceipt, ReceiptHead


@admin.register(ReceiptHead)
class ReceiptHeadAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "description", "is_active")
    search_fields = ("code", "description")


@admin.register(DailyReceipt)
class DailyReceiptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "business_date",
        "institution",
        "receipt_head",
        "amount",
        "entered_by",
        "is_active",
    )
    list_filter = ("is_active", "institution", "business_date")
