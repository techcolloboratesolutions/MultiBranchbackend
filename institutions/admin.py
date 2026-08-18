from django.contrib import admin

from institutions.models import Institution, MainInstitution


@admin.register(MainInstitution)
class MainInstitutionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "is_active")
    search_fields = ("name", "legal_name")


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "main_institution", "city", "is_active")
    list_filter = ("is_active", "main_institution")
    search_fields = ("name",)
