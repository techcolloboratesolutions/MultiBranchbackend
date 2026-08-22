from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path

def health(_request):
    return JsonResponse(
        {
            "status": "ok",
            "database": connection.vendor,
            "db_host": connection.settings_dict.get("HOST") or "",
        }
    )


urlpatterns = [
    path("", health),
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/", include("accounts.urls")),
    path("api/", include("institutions.urls")),
    path("api/", include("receipts.urls")),
    path("api/", include("payments.urls")),
    path("api/", include("partners.urls")),
    path("api/", include("reports.urls")),
    path("api/", include("wages.urls")),
]
