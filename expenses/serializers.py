from rest_framework import serializers

from expenses.models import DailyExpense, ExpenseHead


class ExpenseHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseHead
        fields = ("id", "code", "description", "is_active")


class DailyExpenseSerializer(serializers.ModelSerializer):
    expense_head_name = serializers.CharField(source="expense_head.description", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    entered_by_name = serializers.CharField(source="entered_by.username", read_only=True)

    class Meta:
        model = DailyExpense
        fields = (
            "id",
            "expense_head",
            "expense_head_name",
            "amount",
            "business_date",
            "transaction_date",
            "institution",
            "institution_name",
            "entered_by",
            "entered_by_name",
            "modified_by",
            "modified_date",
            "entry_date",
            "is_active",
        )
        read_only_fields = (
            "entered_by",
            "entered_by_name",
            "modified_by",
            "modified_date",
            "entry_date",
            "transaction_date",
        )
