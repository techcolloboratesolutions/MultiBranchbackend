from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from partners.models import Partner, PartnerGroup, PartnerGroupEntry
from partners.services import (
    validate_group_institution_share_limit,
    validate_institution_single_group,
    validate_partner_once_per_institution,
)


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

    def validate(self, attrs):
        partner_group = attrs.get("partner_group", getattr(self.instance, "partner_group", None))
        institution = attrs.get("institution", getattr(self.instance, "institution", None))
        partner = attrs.get("partner", getattr(self.instance, "partner", None))
        share_percent = attrs.get("share_percent", getattr(self.instance, "share_percent", None))
        is_active = attrs.get("is_active", getattr(self.instance, "is_active", True))
        exclude_pk = getattr(self.instance, "pk", None)
        try:
            validate_institution_single_group(institution, partner_group, exclude_pk=exclude_pk)
            validate_partner_once_per_institution(institution, partner, exclude_pk=exclude_pk)
            validate_group_institution_share_limit(
                partner_group,
                institution,
                share_percent,
                exclude_pk=exclude_pk,
                is_active=is_active,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
        return attrs
