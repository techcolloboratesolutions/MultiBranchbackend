from decimal import Decimal

from django.test import TestCase

from accounts.models import Role, User
from expenses.models import DailyExpense, ExpenseHead
from institutions.models import Institution, MainInstitution


class DailyExpenseTests(TestCase):
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
        self.head = ExpenseHead.objects.create(code="TRAVEL", description="Travel")

    def test_create_expense_uses_decimal(self):
        row = DailyExpense.objects.create(
            expense_head=self.head,
            amount=Decimal("2500.00"),
            business_date="2026-08-01",
            institution=self.inst,
            entered_by=self.user,
        )
        self.assertEqual(row.amount, Decimal("2500.00"))
        self.assertTrue(row.is_active)

    def test_deactivate_does_not_delete(self):
        row = DailyExpense.objects.create(
            expense_head=self.head,
            amount=Decimal("50.00"),
            business_date="2026-08-01",
            institution=self.inst,
            entered_by=self.user,
        )
        row.is_active = False
        row.save()
        self.assertTrue(DailyExpense.objects.filter(pk=row.pk).exists())
        self.assertFalse(DailyExpense.objects.get(pk=row.pk).is_active)
