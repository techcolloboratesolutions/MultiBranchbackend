from rest_framework import serializers

from accounts.models import Role, User
from institutions.models import Institution, MainInstitution


class MainInstitutionBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainInstitution
        fields = ("id", "name")


class InstitutionBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ("id", "name")


class RoleSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source="institution.name", read_only=True)

    class Meta:
        model = Role
        fields = (
            "id",
            "role_code",
            "role_description",
            "institution",
            "institution_name",
            "is_active",
        )


class UserPublicSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.role_code")
    institution = InstitutionBriefSerializer()
    main_institution = MainInstitutionBriefSerializer(source="institution.main_institution")

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "full_name",
            "email",
            "mobile",
            "role",
            "institution",
            "main_institution",
            "status",
            "is_active",
        )


class UserAdminSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source="role.role_code", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "full_name",
            "email",
            "mobile",
            "address",
            "institution",
            "institution_name",
            "role",
            "role_code",
            "status",
            "is_active",
            "password",
        )

    def create(self, validated_data):
        password = validated_data.pop("password", None) or None
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        from django.contrib.auth import authenticate

        username = attrs.get("username")
        password = attrs.get("password")
        user = User.objects.filter(username__iexact=username).first()
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.can_login():
            raise serializers.ValidationError("This account is inactive.")
        authenticated = authenticate(username=user.username, password=password)
        if authenticated is None:
            raise serializers.ValidationError("Invalid username or password.")
        attrs["user"] = authenticated
        return attrs
