from django.urls import include, path
from rest_framework.routers import DefaultRouter

from institutions.views import InstitutionViewSet, MainInstitutionViewSet

router = DefaultRouter()
router.register("main-institutions", MainInstitutionViewSet, basename="main-institution")
router.register("institutions", InstitutionViewSet, basename="institution")

urlpatterns = [
    path("", include(router.urls)),
]
