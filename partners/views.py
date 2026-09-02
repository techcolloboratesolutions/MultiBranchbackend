from rest_framework import viewsets

from accounts.permissions import IsAdminOrReadOnlyManager
from accounts.scoping import apply_institution_filter, scoped_institution_id
from partners.models import Partner, PartnerGroup, PartnerGroupEntry
from partners.serializers import (
    PartnerGroupEntrySerializer,
    PartnerGroupSerializer,
    PartnerSerializer,
)


class PartnerViewSet(viewsets.ModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    permission_classes = [IsAdminOrReadOnlyManager]

    def get_queryset(self):
        qs = super().get_queryset()
        in_group = str(self.request.query_params.get("in_group") or "").lower() in ("1", "true", "yes")
        if not in_group:
            return qs
        institution_id = scoped_institution_id(self.request)
        if institution_id is None:
            return qs.none()
        return qs.filter(
            group_entries__institution_id=institution_id,
            group_entries__is_active=True,
            is_active=True,
        ).distinct()


class PartnerGroupViewSet(viewsets.ModelViewSet):
    queryset = PartnerGroup.objects.all()
    serializer_class = PartnerGroupSerializer
    permission_classes = [IsAdminOrReadOnlyManager]


class PartnerGroupEntryViewSet(viewsets.ModelViewSet):
    queryset = PartnerGroupEntry.objects.select_related(
        "partner_group", "institution", "partner"
    ).all()
    serializer_class = PartnerGroupEntrySerializer
    permission_classes = [IsAdminOrReadOnlyManager]

    def get_queryset(self):
        return apply_institution_filter(super().get_queryset(), self.request)
