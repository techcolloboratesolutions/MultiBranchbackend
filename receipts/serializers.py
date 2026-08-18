from rest_framework import serializers

from receipts.models import DailyReceipt, ReceiptHead


class ReceiptHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptHead
        fields = ("id", "code", "description", "is_active")


class DailyReceiptSerializer(serializers.ModelSerializer):
    receipt_head_name = serializers.CharField(source="receipt_head.description", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    entered_by_name = serializers.CharField(source="entered_by.username", read_only=True)

    class Meta:
        model = DailyReceipt
        fields = (
            "id",
            "receipt_head",
            "receipt_head_name",
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
