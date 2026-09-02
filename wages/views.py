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


def _preview_or_error(institution_id, year, month):
    try:
        return preview_wages(institution_id, year, month)
    except DjangoValidationError as exc:
        raise ValidationError(exc.messages if hasattr(exc, "messages") else str(exc))


class WageCalculateView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        year, month, institution_id = _period(request, require_institution=True)
        return Response(_serialize_preview(_preview_or_error(institution_id, year, month)))

    def post(self, request):
        year, month, institution_id = _period(request, require_institution=True)
        return Response(_serialize_preview(_preview_or_error(institution_id, year, month)))


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
        data = _preview_or_error(institution_id, year, month)
        inst_name = Institution.objects.get(pk=institution_id).name
        wb = Workbook()
        ws = wb.active
        ws.title = "Wages"
        ws.append(
            [
                "Institution",
                "Year",
                "Month",
                "Total Sales",
                "Total Purchase",
                "Total Expense",
                "Total Business",
                "Balance",
                "Group",
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
                    float(data["total_sales"]),
                    float(data["total_purchase"]),
                    float(data["total_expense"]),
                    float(data["total_business"]),
                    float(data["total_balance"]),
                    row.get("group_name", ""),
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
        "total_sales": str(data["total_sales"]),
        "total_purchase": str(data["total_purchase"]),
        "total_expense": str(data["total_expense"]),
        "total_business": str(data["total_business"]),
        "total_balance": str(data["total_balance"]),
        "share_total": str(data["share_total"]),
        "group_name": data.get("group_name") or "",
        "partners": [
            {
                "partner_id": row["partner_id"],
                "partner_name": row["partner_name"],
                "group_name": row.get("group_name", ""),
                "share_percent": str(row["share_percent"]),
                "partner_wage_amount": str(row["partner_wage_amount"]),
                "partner_mobile": row.get("partner_mobile") or "",
            }
            for row in data["partners"]
        ],
    }
