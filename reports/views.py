from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from datetime import date as date_type

from accounts.permissions import IsAdminOrManager, IsAdminRole
from accounts.scoping import scoped_institution_id
from reports.services import (
    daily_breakdown,
    institution_business,
    institution_date_head_matrix,
    institution_day_totals,
    monthly_head_matrix,
    monthly_trend,
    period_totals,
    sum_payments,
    sum_receipts,
)
from institutions.models import Institution
from django.utils import timezone

from core.money import calculate_total_business


class MonthlyReportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        year, month, institution_id = _period_params(request)
        matrix = monthly_head_matrix(institution_id, year, month)
        totals = matrix["totals"]
        payload = {
            "year": year,
            "month": month,
            "institution_id": institution_id,
            "receipt_heads": [
                {"id": head.id, "code": head.code, "description": head.description}
                for head in matrix["receipt_heads"]
            ],
            "payment_heads": [
                {"id": head.id, "code": head.code, "description": head.description}
                for head in matrix["payment_heads"]
            ],
            "rows": [
                {
                    "date": row["date"].isoformat(),
                    "receipts": {key: str(value) for key, value in row["receipts"].items()},
                    "payments": {key: str(value) for key, value in row["payments"].items()},
                    "receipt": str(row["receipt"]),
                    "payment": str(row["payment"]),
                    "business": str(row["business"]),
                }
                for row in matrix["rows"]
            ],
            "receipt_head_totals": {
                str(head_id): str(amount) for head_id, amount in matrix["receipt_head_totals"].items()
            },
            "payment_head_totals": {
                str(head_id): str(amount) for head_id, amount in matrix["payment_head_totals"].items()
            },
            "total_receipt": str(totals["total_receipt"]),
            "total_payment": str(totals["total_payment"]),
            "total_business": str(totals["total_business"]),
        }
        return Response(payload)


class MonthlyReportExportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        year, month, institution_id = _period_params(request)
        matrix = monthly_head_matrix(institution_id, year, month)
        totals = matrix["totals"]
        inst_name = "ALL"
        if institution_id:
            inst_name = Institution.objects.get(pk=institution_id).name

        receipt_heads = matrix["receipt_heads"]
        payment_heads = matrix["payment_heads"]
        wb = Workbook()
        ws = wb.active
        ws.title = "Monthly"
        header = (
            ["Institution", "Date"]
            + [f"{head.code} - {head.description}" for head in receipt_heads]
            + ["Total Receipt"]
            + [f"{head.code} - {head.description}" for head in payment_heads]
            + ["Total Payment", "Business"]
        )
        ws.append(header)
        for row in matrix["rows"]:
            line = [inst_name, row["date"].isoformat()]
            for head in receipt_heads:
                line.append(float(row["receipts"].get(str(head.id), 0)))
            line.append(float(row["receipt"]))
            for head in payment_heads:
                line.append(float(row["payments"].get(str(head.id), 0)))
            line.append(float(row["payment"]))
            line.append(float(row["business"]))
            ws.append(line)
        total_line = [inst_name, "TOTAL"]
        for head in receipt_heads:
            total_line.append(float(matrix["receipt_head_totals"][head.id]))
        total_line.append(float(totals["total_receipt"]))
        for head in payment_heads:
            total_line.append(float(matrix["payment_head_totals"][head.id]))
        total_line.append(float(totals["total_payment"]))
        total_line.append(float(totals["total_business"]))
        ws.append(total_line)
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="monthly-{year}-{month:02d}.xlsx"'
        return response


class DayByInstitutionReportView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        raw = (request.query_params.get("date") or "").strip()
        if not raw:
            return Response({"detail": "date is required (YYYY-MM-DD)."}, status=400)
        try:
            day = date_type.fromisoformat(raw)
        except ValueError:
            return Response({"detail": "Invalid date."}, status=400)
        matrix = institution_date_head_matrix(day)
        totals = matrix["totals"]
        return Response(
            {
                "date": day.isoformat(),
                "receipt_heads": [
                    {"id": head.id, "code": head.code, "description": head.description}
                    for head in matrix["receipt_heads"]
                ],
                "payment_heads": [
                    {"id": head.id, "code": head.code, "description": head.description}
                    for head in matrix["payment_heads"]
                ],
                "rows": [
                    {
                        "institution_id": row["institution_id"],
                        "institution_name": row["institution_name"],
                        "receipts": {key: str(value) for key, value in row["receipts"].items()},
                        "payments": {key: str(value) for key, value in row["payments"].items()},
                        "receipt": str(row["receipt"]),
                        "payment": str(row["payment"]),
                        "business": str(row["business"]),
                    }
                    for row in matrix["rows"]
                ],
                "receipt_head_totals": {
                    str(head_id): str(amount) for head_id, amount in matrix["receipt_head_totals"].items()
                },
                "payment_head_totals": {
                    str(head_id): str(amount) for head_id, amount in matrix["payment_head_totals"].items()
                },
                "total_receipt": str(totals["total_receipt"]),
                "total_payment": str(totals["total_payment"]),
                "total_business": str(totals["total_business"]),
            }
        )


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        user = request.user
        institution_id = scoped_institution_id(request)
        today_receipt = sum_receipts(institution_id, today, today)
        today_payment = sum_payments(institution_id, today, today)
        month_totals = period_totals(institution_id, today.year, today.month)
        rows, _ = daily_breakdown(institution_id, today.year, today.month)
        trend = monthly_trend(institution_id, today, months=12)

        scope_name = user.institution.name
        if user.is_admin_role and institution_id is None:
            scope_name = "ALL branches"

        payload = {
            "role": user.role_code,
            "scope": "all" if institution_id is None else "institution",
            "institution": {
                "id": institution_id or user.institution_id,
                "name": scope_name,
            },
            "today": {
                "receipt": str(today_receipt),
                "payment": str(today_payment),
                "business": str(calculate_total_business(today_receipt, today_payment)),
            },
            "month": {
                "receipt": str(month_totals["total_receipt"]),
                "payment": str(month_totals["total_payment"]),
                "business": str(month_totals["total_business"]),
            },
            "daily_series": [
                {
                    "date": row["date"].isoformat(),
                    "label": row["date"].strftime("%d %b"),
                    "receipt": float(row["receipt"]),
                    "payment": float(row["payment"]),
                    "business": float(row["business"]),
                }
                for row in rows
            ],
            "monthly_series": [
                {
                    "label": row["label"],
                    "year": row["year"],
                    "month": row["month"],
                    "receipt": float(row["receipt"]),
                    "payment": float(row["payment"]),
                    "business": float(row["business"]),
                }
                for row in trend
            ],
        }

        if user.is_admin_role:
            payload["institutions_total"] = Institution.objects.count()
            payload["institutions_active"] = Institution.objects.filter(is_active=True).count()
            payload["institution_series"] = [
                {
                    "id": row["institution_id"],
                    "name": row["institution_name"],
                    "business": float(row["business"]),
                    "receipt": float(row["receipt"]),
                    "payment": float(row["payment"]),
                }
                for row in institution_business(today.year, today.month)
            ]
            payload["institution_today"] = [
                {
                    "id": row["institution_id"],
                    "name": row["institution_name"],
                    "business": float(row["business"]),
                    "receipt": float(row["receipt"]),
                    "payment": float(row["payment"]),
                }
                for row in institution_day_totals(today)
            ]

        return Response(payload)


def _period_params(request):
    today = timezone.localdate()
    year = int(request.query_params.get("year") or today.year)
    month = int(request.query_params.get("month") or today.month)
    institution_id = scoped_institution_id(request)
    return year, month, institution_id
