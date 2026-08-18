from rest_framework import viewsets

from accounts.permissions import IsAdminOrReadOnlyManager
from accounts.scoping import apply_institution_filter
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
