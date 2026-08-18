from django.contrib import admin

from wages.models import BusinessWage


@admin.register(BusinessWage)
class BusinessWageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "institution",
        "wages_year",
        "wages_month",
        "partner",
        "total_business",
        "business_percent",
        "partner_wage_amount",
        "is_active",
    )
    list_filter = ("wages_year", "wages_month", "institution", "is_active")
