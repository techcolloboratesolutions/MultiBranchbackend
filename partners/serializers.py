from rest_framework import serializers

from partners.models import Partner, PartnerGroup, PartnerGroupEntry


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ("id", "name", "mobile", "email", "address", "is_active")


class PartnerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerGroup
        fields = ("id", "name", "is_active", "whatsapp_group", "is_profit_sharing")


class PartnerGroupEntrySerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source="partner.name", read_only=True)
    group_name = serializers.CharField(source="partner_group.name", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)

    class Meta:
        model = PartnerGroupEntry
        fields = (
            "id",
            "partner_group",
            "group_name",
            "institution",
            "institution_name",
            "partner",
            "partner_name",
            "share_percent",
            "is_active",
        )
