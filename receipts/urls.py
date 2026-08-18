from django.urls import include, path
from rest_framework.routers import DefaultRouter

from receipts.views import DailyReceiptViewSet, ReceiptHeadViewSet

router = DefaultRouter()
router.register("receipt-heads", ReceiptHeadViewSet, basename="receipt-head")
router.register("receipts", DailyReceiptViewSet, basename="receipt")

urlpatterns = [
    path("", include(router.urls)),
]
