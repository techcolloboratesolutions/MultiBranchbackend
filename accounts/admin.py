from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import PasswordResetToken, Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "role_code", "role_description", "institution", "is_active")
    list_filter = ("is_active", "role_code")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = (
        "username",
        "full_name",
        "institution",
        "role",
        "status",
        "is_active",
    )
    list_filter = ("status", "is_active", "role", "institution")
    search_fields = ("username", "full_name", "email")
    ordering = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Profile", {"fields": ("full_name", "email", "mobile", "address")}),
        ("Organization", {"fields": ("institution", "role", "status")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "full_name",
                    "institution",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "expires_at", "used_at")
    readonly_fields = ("token_hash", "created_at")
