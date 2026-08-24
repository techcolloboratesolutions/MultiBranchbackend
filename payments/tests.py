from decimal import Decimal

from django.test import TestCase

from accounts.models import Role, User
from institutions.models import Institution, MainInstitution
from payments.models import DailyPayment, PaymentHead


class DailyPaymentTests(TestCase):
    def setUp(self):
        main = MainInstitution.objects.create(name="Horizon Group")
        self.inst = Institution.objects.create(name="Head Office", main_institution=main)
        role = Role.objects.create(role_code=Role.Code.MANAGER, role_description="Manager")
        self.user = User.objects.create_user(
            username="manager01",
            password="ChangeMeManager123!",
            full_name="Manager 01",
            institution=self.inst,
            role=role,
        )
        self.head = PaymentHead.objects.create(code="RENT", description="Rent")

    def test_create_and_deactivate(self):
        pay = DailyPayment.objects.create(
            payment_head=self.head,
            amount=Decimal("400000.00"),
            business_date="2026-08-01",
            institution=self.inst,
            entered_by=self.user,
        )
        pay.is_active = False
        pay.save()
        self.assertTrue(DailyPayment.objects.filter(pk=pay.pk).exists())
        self.assertFalse(pay.is_active)


class PaymentEntrySheetTests(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient

        main = MainInstitution.objects.create(name="Horizon Group")
        self.inst = Institution.objects.create(name="Head Office", main_institution=main)
        role = Role.objects.create(role_code=Role.Code.MANAGER, role_description="Manager")
        self.user = User.objects.create_user(
            username="manager01",
            password="ChangeMeManager123!",
            full_name="Manager 01",
            institution=self.inst,
            role=role,
        )
        self.rent = PaymentHead.objects.create(
            code="RENT",
            description="Rent",
            recurring_type=PaymentHead.RecurringType.MONTHLY,
        )
        PaymentHead.objects.create(code="SAL", description="Salary")
        PaymentHead.objects.create(code="OLD", description="Inactive", is_active=False)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_entry_sheet_defaults_to_daily_column_only(self):
        response = self.client.get(
            "/api/payments/entry-sheet/",
            {"business_date": "2026-08-17", "institution_id": self.inst.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["layout"], "two_column")
        self.assertTrue(response.data["daily_selected"])
        self.assertFalse(response.data["monthly_selected"])
        self.assertEqual([row["code"] for row in response.data["daily_rows"]], ["SAL"])
        self.assertEqual(response.data["monthly_rows"], [])
        self.assertEqual([row["code"] for row in response.data["rows"]], ["SAL"])
        self.assertNotIn("OLD", [row["code"] for row in response.data["rows"]])

    def test_entry_sheet_monthly_adds_second_column_daily_stays(self):
        response = self.client.get(
            "/api/payments/entry-sheet/",
            {
                "business_date": "2026-08-17",
                "institution_id": self.inst.id,
                "recurring_type": "Monthly",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["daily_selected"])
        self.assertTrue(response.data["monthly_selected"])
        self.assertEqual([row["code"] for row in response.data["daily_rows"]], ["SAL"])
        self.assertEqual([row["code"] for row in response.data["monthly_rows"]], ["RENT"])
        self.assertEqual(response.data["monthly_rows"][0]["recurring_type"], "Monthly")
        self.assertEqual([row["code"] for row in response.data["rows"]], ["SAL", "RENT"])

    def test_entry_sheet_both_columns_when_daily_and_monthly_checked(self):
        response = self.client.get(
            "/api/payments/entry-sheet/",
            {
                "business_date": "2026-08-17",
                "institution_id": self.inst.id,
                "monthly": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["daily_selected"])
        self.assertTrue(response.data["monthly_selected"])
        self.assertEqual([row["code"] for row in response.data["daily_rows"]], ["SAL"])
        self.assertEqual([row["code"] for row in response.data["monthly_rows"]], ["RENT"])
        self.assertEqual([row["code"] for row in response.data["rows"]], ["SAL", "RENT"])

    def test_bulk_skips_inactive_heads(self):
        inactive = PaymentHead.objects.get(code="OLD")
        response = self.client.post(
            "/api/payments/bulk/",
            {
                "institution": self.inst.id,
                "business_date": "2026-08-17",
                "lines": [
                    {"payment_head": self.rent.id, "amount": "1500.00"},
                    {"payment_head": inactive.id, "amount": "999.00"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DailyPayment.objects.filter(is_active=True).count(), 1)
        self.assertFalse(DailyPayment.objects.filter(payment_head=inactive).exists())
