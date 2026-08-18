from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from institutions.models import Institution, MainInstitution
from payments.models import DailyPayment, PaymentHead
from receipts.models import DailyReceipt, ReceiptHead
from reports.services import monthly_head_matrix, monthly_trend


class MonthlyHeadReportTests(TestCase):
    def setUp(self):
        main = MainInstitution.objects.create(name="Horizon Group")
        self.inst = Institution.objects.create(name="Head Office", main_institution=main)
        role = Role.objects.create(role_code=Role.Code.MANAGER, role_description="Manager")
        self.user = User.objects.create_user(
            username="manager01",
            password="ChangeMeManager123!",
            full_name="Manager",
            institution=self.inst,
            role=role,
        )
        self.cash = ReceiptHead.objects.create(code="CASH", description="Cash")
        self.bank = ReceiptHead.objects.create(code="BANK", description="Bank")
        ReceiptHead.objects.create(code="OLD", description="Inactive", is_active=False)
        self.rent = PaymentHead.objects.create(code="RENT", description="Rent")
        self.sal = PaymentHead.objects.create(code="SAL", description="Salary")
        DailyReceipt.objects.create(
            receipt_head=self.cash,
            amount=Decimal("50000.00"),
            business_date="2026-08-01",
            institution=self.inst,
            entered_by=self.user,
        )
        DailyReceipt.objects.create(
            receipt_head=self.bank,
            amount=Decimal("10000.00"),
            business_date="2026-08-01",
            institution=self.inst,
            entered_by=self.user,
        )
        DailyReceipt.objects.create(
            receipt_head=self.cash,
            amount=Decimal("20000.00"),
            business_date="2026-08-02",
            institution=self.inst,
            entered_by=self.user,
        )
        DailyPayment.objects.create(
            payment_head=self.rent,
            amount=Decimal("15000.00"),
            business_date="2026-08-01",
            institution=self.inst,
            entered_by=self.user,
        )

    def test_head_columns_and_sums(self):
        matrix = monthly_head_matrix(self.inst.id, 2026, 8)
        codes = [head.code for head in matrix["receipt_heads"]]
        self.assertEqual(codes, ["BANK", "CASH"])
        self.assertEqual(matrix["receipt_head_totals"][self.cash.id], Decimal("70000.00"))
        self.assertEqual(matrix["receipt_head_totals"][self.bank.id], Decimal("10000.00"))
        self.assertEqual(matrix["payment_head_totals"][self.rent.id], Decimal("15000.00"))
        self.assertEqual(matrix["totals"]["total_business"], Decimal("65000.00"))

    def test_monthly_api_includes_heads(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.get("/api/reports/monthly/", {"year": 2026, "month": 8})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([head["code"] for head in response.data["receipt_heads"]], ["BANK", "CASH"])
        self.assertIn(str(self.cash.id), response.data["receipt_head_totals"])

    def test_monthly_trend_has_twelve_months(self):
        from datetime import date

        series = monthly_trend(self.inst.id, date(2026, 8, 17), months=12)
        self.assertEqual(len(series), 12)
        self.assertEqual(series[-1]["label"], "Aug 2026")
        self.assertEqual(series[-1]["business"], Decimal("65000.00"))
