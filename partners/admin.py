from django.contrib import admin

from partners.models import Partner, PartnerGroup, PartnerGroupEntry


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "mobile", "email", "is_active")
    search_fields = ("name", "email")


@admin.register(PartnerGroup)
class PartnerGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_profit_sharing", "whatsapp_group", "is_active")


@admin.register(PartnerGroupEntry)
class PartnerGroupEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "partner_group",
        "institution",
        "partner",
        "share_percent",
        "is_active",
    )
    list_filter = ("partner_group", "institution", "is_active")
