from rest_framework import serializers

from institutions.models import Institution, MainInstitution


class MainInstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainInstitution
        fields = (
            "id",
            "name",
            "place",
            "address",
            "po_box",
            "phone",
            "fax",
            "email",
            "legal_name",
            "country",
            "state",
            "city",
            "district",
            "is_active",
        )


class InstitutionSerializer(serializers.ModelSerializer):
    main_institution_name = serializers.CharField(source="main_institution.name", read_only=True)

    class Meta:
        model = Institution
        fields = (
            "id",
            "name",
            "main_institution",
            "main_institution_name",
            "address",
            "po_box",
            "phone1",
            "mobile",
            "fax",
            "email",
            "contact_person",
            "contact_number",
            "country",
            "state",
            "city",
            "district",
            "longitude",
            "latitude",
            "is_active",
        )
