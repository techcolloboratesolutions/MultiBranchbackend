from django.urls import include, path
from rest_framework.routers import DefaultRouter

from partners.views import PartnerGroupEntryViewSet, PartnerGroupViewSet, PartnerViewSet

router = DefaultRouter()
router.register("partners", PartnerViewSet, basename="partner")
router.register("partner-groups", PartnerGroupViewSet, basename="partner-group")
router.register("partner-group-entries", PartnerGroupEntryViewSet, basename="partner-group-entry")

urlpatterns = [
    path("", include(router.urls)),
]
