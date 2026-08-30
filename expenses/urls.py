from django.urls import include, path
from rest_framework.routers import DefaultRouter

from expenses.views import DailyExpenseViewSet, ExpenseHeadViewSet

router = DefaultRouter()
router.register("expense-heads", ExpenseHeadViewSet, basename="expense-head")
router.register("expenses", DailyExpenseViewSet, basename="expense")

urlpatterns = [
    path("", include(router.urls)),
]
