from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminRole
from accounts.scoping import scoped_institution_id
from institutions.models import Institution, MainInstitution
from institutions.serializers import InstitutionSerializer, MainInstitutionSerializer


class MainInstitutionViewSet(viewsets.ModelViewSet):
    queryset = MainInstitution.objects.all()
    serializer_class = MainInstitutionSerializer
    permission_classes = [IsAdminRole]


class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.select_related("main_institution").all()
    serializer_class = InstitutionSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_manager_role", False):
            return qs.filter(pk=user.institution_id)
        institution_id = scoped_institution_id(self.request)
        if institution_id is not None:
            return qs.filter(pk=institution_id)
        return qs
