from decimal import Decimal

from django.test import TestCase

from accounts.models import Role, User
from institutions.models import Institution, MainInstitution
from receipts.models import DailyReceipt, ReceiptHead


class DailyReceiptTests(TestCase):
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
        self.head = ReceiptHead.objects.create(code="CASH", description="Cash Collection")

    def test_create_receipt_uses_decimal(self):
        rec = DailyReceipt.objects.create(
            receipt_head=self.head,
            amount=Decimal("1000000.00"),
            business_date="2026-08-01",
            institution=self.inst,
            entered_by=self.user,
        )
        self.assertEqual(rec.amount, Decimal("1000000.00"))
        self.assertTrue(rec.is_active)

    def test_deactivate_does_not_delete(self):
        rec = DailyReceipt.objects.create(
            receipt_head=self.head,
            amount=Decimal("50.00"),
            business_date="2026-08-01",
            institution=self.inst,
            entered_by=self.user,
        )
        rec.is_active = False
        rec.save()
        self.assertTrue(DailyReceipt.objects.filter(pk=rec.pk).exists())
        self.assertFalse(DailyReceipt.objects.get(pk=rec.pk).is_active)
