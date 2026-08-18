from django.urls import path

from reports.views import DashboardView, MonthlyReportExportView, MonthlyReportView

urlpatterns = [
    path("reports/monthly/", MonthlyReportView.as_view(), name="reports-monthly"),
    path("reports/monthly/export/", MonthlyReportExportView.as_view(), name="reports-monthly-export"),
    path("reports/dashboard/", DashboardView.as_view(), name="reports-dashboard"),
]
