from rest_framework import serializers

from wages.models import BusinessWage


class BusinessWageSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source="partner.name", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)

    class Meta:
        model = BusinessWage
        fields = (
            "id",
            "institution",
            "institution_name",
            "wages_month",
            "wages_year",
            "total_receipt",
            "total_payment",
            "total_business",
            "business_percent",
            "partner",
            "partner_name",
            "partner_wage_amount",
            "is_active",
        )
