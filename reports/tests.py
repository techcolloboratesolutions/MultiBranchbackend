from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from expenses.models import DailyExpense, ExpenseHead
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
        self.travel = ExpenseHead.objects.create(code="TRAVEL", description="Travel")
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
        DailyExpense.objects.create(
            expense_head=self.travel,
            amount=Decimal("5000.00"),
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
        self.assertEqual(matrix["expense_head_totals"][self.travel.id], Decimal("5000.00"))
        self.assertEqual(matrix["totals"]["total_business"], Decimal("95000.00"))
        self.assertEqual(matrix["totals"]["total_balance"], Decimal("90000.00"))

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
        self.assertEqual(series[-1]["business"], Decimal("95000.00"))
        self.assertEqual(series[-1]["balance"], Decimal("90000.00"))


class AdminDashboardAllTests(TestCase):
    def setUp(self):
        from django.utils import timezone

        main = MainInstitution.objects.create(name="Horizon Group")
        self.a = Institution.objects.create(name="Branch A", main_institution=main)
        self.b = Institution.objects.create(name="Branch B", main_institution=main)
        admin_role = Role.objects.create(role_code=Role.Code.ADMIN, role_description="Admin")
        manager_role = Role.objects.create(role_code=Role.Code.MANAGER, role_description="Manager")
        self.admin = User.objects.create_user(
            username="admin",
            password="ChangeMeAdmin123!",
            full_name="Admin",
            institution=self.a,
            role=admin_role,
            is_staff=True,
        )
        self.manager = User.objects.create_user(
            username="manager01",
            password="ChangeMeManager123!",
            full_name="Manager",
            institution=self.a,
            role=manager_role,
        )
        cash = ReceiptHead.objects.create(code="CASH", description="Cash")
        rent = PaymentHead.objects.create(code="RENT", description="Rent")
        today = timezone.localdate()
        DailyReceipt.objects.create(
            receipt_head=cash,
            amount=Decimal("100.00"),
            business_date=today,
            institution=self.a,
            entered_by=self.manager,
        )
        DailyPayment.objects.create(
            payment_head=rent,
            amount=Decimal("40.00"),
            business_date=today,
            institution=self.b,
            entered_by=self.manager,
        )

    def test_all_scope_includes_today_by_branch_and_monthly_table(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        response = client.get("/api/reports/dashboard/")
        self.assertEqual(response.status_code, 200)
        names = [row["name"] for row in response.data["institution_today"]]
        self.assertIn("Branch A", names)
        self.assertIn("Branch B", names)
        today_a = next(row for row in response.data["institution_today"] if row["name"] == "Branch A")
        today_b = next(row for row in response.data["institution_today"] if row["name"] == "Branch B")
        self.assertEqual(today_a["receipt"], 100.0)
        self.assertEqual(today_b["payment"], 40.0)
        monthly_names = [row["name"] for row in response.data["institution_series"]]
        self.assertEqual(monthly_names, ["Branch A", "Branch B"])

    def test_day_by_institution_report_lists_all_branches(self):
        from django.utils import timezone

        client = APIClient()
        client.force_authenticate(self.admin)
        today = timezone.localdate().isoformat()
        response = client.get("/api/reports/monthly/by-institution/", {"date": today})
        self.assertEqual(response.status_code, 200)
        names = [row["institution_name"] for row in response.data["rows"]]
        self.assertEqual(names, ["Branch A", "Branch B"])
        row_a = next(row for row in response.data["rows"] if row["institution_name"] == "Branch A")
        row_b = next(row for row in response.data["rows"] if row["institution_name"] == "Branch B")
        self.assertEqual(row_a["receipt"], "100.00")
        self.assertEqual(row_b["payment"], "40.00")

    def test_day_by_institution_forbidden_for_manager(self):
        from django.utils import timezone

        client = APIClient()
        client.force_authenticate(self.manager)
        today = timezone.localdate().isoformat()
        response = client.get("/api/reports/monthly/by-institution/", {"date": today})
        self.assertEqual(response.status_code, 403)
