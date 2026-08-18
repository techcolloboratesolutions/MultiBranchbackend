from django.urls import include, path
from rest_framework.routers import DefaultRouter

from payments.views import DailyPaymentViewSet, PaymentHeadViewSet

router = DefaultRouter()
router.register("payment-heads", PaymentHeadViewSet, basename="payment-head")
router.register("payments", DailyPaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
