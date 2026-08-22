from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    db = settings.DATABASES.get("default", {})
    engine = str(db.get("ENGINE") or "").rsplit(".", 1)[-1]
    return JsonResponse(
        {
            "status": "ok",
            "database": engine,
            "db_host": db.get("HOST") or "",
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
