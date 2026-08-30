from django.contrib import admin

from expenses.models import DailyExpense, ExpenseHead


@admin.register(ExpenseHead)
class ExpenseHeadAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "description", "is_active")
    search_fields = ("code", "description")


@admin.register(DailyExpense)
class DailyExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "business_date",
        "institution",
        "expense_head",
        "amount",
        "entered_by",
        "is_active",
    )
    list_filter = ("is_active", "institution", "business_date")
