from django.urls import path

from wages.views import WageCalculateView, WageExportView, WageSaveView

urlpatterns = [
    path("wages/calculate/", WageCalculateView.as_view(), name="wages-calculate"),
    path("wages/save/", WageSaveView.as_view(), name="wages-save"),
    path("wages/export/", WageExportView.as_view(), name="wages-export"),
]
