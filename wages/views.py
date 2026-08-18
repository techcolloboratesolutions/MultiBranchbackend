from io import BytesIO

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrManager
from accounts.scoping import INSTITUTION_FORBIDDEN, scoped_institution_id
from institutions.models import Institution
from wages.services import preview_wages, save_wages


def _period(request, require_institution=False):
    today = timezone.localdate()
    year = int(request.query_params.get("year") or request.data.get("year") or today.year)
    month = int(request.query_params.get("month") or request.data.get("month") or today.month)
    institution_id = scoped_institution_id(request)
    if require_institution and institution_id is None:
        raise ValidationError("Select a specific institution to calculate partner wages.")
    return year, month, institution_id


class WageCalculateView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        year, month, institution_id = _period(request, require_institution=True)
        data = preview_wages(institution_id, year, month)
        return Response(_serialize_preview(data))

    def post(self, request):
        year, month, institution_id = _period(request, require_institution=True)
        data = preview_wages(institution_id, year, month)
        return Response(_serialize_preview(data))


class WageSaveView(APIView):
    permission_classes = [IsAdminOrManager]

    def post(self, request):
        year, month, institution_id = _period(request, require_institution=True)
        if getattr(request.user, "is_manager_role", False) and institution_id != request.user.institution_id:
            raise PermissionDenied(detail=INSTITUTION_FORBIDDEN)
        institution = Institution.objects.get(pk=institution_id)
        try:
            preview, _saved = save_wages(institution, year, month, request.user)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages if hasattr(exc, "messages") else str(exc))
        payload = _serialize_preview(preview)
        payload["saved"] = True
        return Response(payload)


class WageExportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        year, month, institution_id = _period(request, require_institution=True)
        data = preview_wages(institution_id, year, month)
        inst_name = Institution.objects.get(pk=institution_id).name
        wb = Workbook()
        ws = wb.active
        ws.title = "Wages"
        ws.append(
            [
                "Institution",
                "Year",
                "Month",
                "Total Receipt",
                "Total Payment",
                "Total Business",
                "Partner",
                "Share %",
                "Partner Wage",
            ]
        )
        for row in data["partners"]:
            ws.append(
                [
                    inst_name,
                    year,
                    month,
                    float(data["total_receipt"]),
                    float(data["total_payment"]),
                    float(data["total_business"]),
                    row["partner_name"],
                    float(row["share_percent"]),
                    float(row["partner_wage_amount"]),
                ]
            )
        buffer = BytesIO()
        wb.save(buffer)
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="wages-{year}-{month:02d}.xlsx"'
        return response


def _serialize_preview(data):
    return {
        "institution_id": data["institution_id"],
        "year": data["year"],
        "month": data["month"],
        "total_receipt": str(data["total_receipt"]),
        "total_payment": str(data["total_payment"]),
        "total_business": str(data["total_business"]),
        "share_total": str(data["share_total"]),
        "partners": [
            {
                "partner_id": row["partner_id"],
                "partner_name": row["partner_name"],
                "share_percent": str(row["share_percent"]),
                "partner_wage_amount": str(row["partner_wage_amount"]),
            }
            for row in data["partners"]
        ],
    }
