from rest_framework import serializers

from payments.models import DailyPayment, PaymentHead


class PaymentHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHead
        fields = ("id", "code", "description", "is_active", "recurring_type")


class DailyPaymentSerializer(serializers.ModelSerializer):
    payment_head_name = serializers.CharField(source="payment_head.description", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    entered_by_name = serializers.CharField(source="entered_by.username", read_only=True)

    class Meta:
        model = DailyPayment
        fields = (
            "id",
            "payment_head",
            "payment_head_name",
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
