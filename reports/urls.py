from django.urls import path

from reports.views import (
    BranchWindowView,
    DashboardView,
    DayByInstitutionReportView,
    MonthlyReportExportView,
    MonthlyReportView,
    PeriodicSalesPurchaseView,
)

urlpatterns = [
    path("reports/monthly/", MonthlyReportView.as_view(), name="reports-monthly"),
    path("reports/monthly/by-institution/", DayByInstitutionReportView.as_view(), name="reports-monthly-by-institution"),
    path("reports/monthly/export/", MonthlyReportExportView.as_view(), name="reports-monthly-export"),
    path("reports/periodic/", PeriodicSalesPurchaseView.as_view(), name="reports-periodic"),
    path("reports/branch-window/", BranchWindowView.as_view(), name="reports-branch-window"),
    path("reports/dashboard/", DashboardView.as_view(), name="reports-dashboard"),
]
