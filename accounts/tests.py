from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from institutions.models import Institution, MainInstitution
from receipts.models import DailyReceipt, ReceiptHead


class AuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.main = MainInstitution.objects.create(name="Horizon Group")
        self.inst1 = Institution.objects.create(name="Branch 1", main_institution=self.main)
        self.inst2 = Institution.objects.create(name="Branch 2", main_institution=self.main)
        self.admin_role = Role.objects.create(role_code=Role.Code.ADMIN, role_description="Admin")
        self.manager_role = Role.objects.create(role_code=Role.Code.MANAGER, role_description="Manager")
        self.admin = User.objects.create_user(
            username="admin",
            password="ChangeMeAdmin123!",
            full_name="Admin",
            institution=self.inst1,
            role=self.admin_role,
            is_staff=True,
        )
        self.manager = User.objects.create_user(
            username="manager01",
            password="ChangeMeManager123!",
            full_name="Manager",
            institution=self.inst1,
            role=self.manager_role,
        )

    def test_valid_login(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "manager01", "password": "ChangeMeManager123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["role"], "MANAGER")

    def test_invalid_login(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "manager01", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_inactive_user(self):
        self.manager.is_active = False
        self.manager.save()
        response = self.client.post(
            "/api/auth/login/",
            {"username": "manager01", "password": "ChangeMeManager123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_can_list_all_institutions(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/institutions/?page_size=100")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 2)

    def test_manager_sees_own_institution_only(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/institutions/?page_size=100")
        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [self.inst1.id])

    def test_manager_cannot_access_other_institution_receipts(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get(f"/api/receipts/?institution_id={self.inst2.id}")
        self.assertEqual(response.status_code, 403)


class ReceiptApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        main = MainInstitution.objects.create(name="Horizon Group")
        self.inst = Institution.objects.create(name="Branch 1", main_institution=main)
        role = Role.objects.create(role_code=Role.Code.MANAGER, role_description="Manager")
        self.user = User.objects.create_user(
            username="manager01",
            password="ChangeMeManager123!",
            full_name="Manager",
            institution=self.inst,
            role=role,
        )
        self.head = ReceiptHead.objects.create(code="CASH", description="Cash")
        self.client.force_authenticate(self.user)

    def test_create_update_deactivate(self):
        create = self.client.post(
            "/api/receipts/",
            {
                "receipt_head": self.head.id,
                "amount": "50000.00",
                "business_date": "2026-08-01",
                "institution": self.inst.id,
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        pk = create.data["id"]
        update = self.client.patch(f"/api/receipts/{pk}/", {"amount": "55000.00"}, format="json")
        self.assertEqual(update.status_code, 200)
        deactivate = self.client.post(f"/api/receipts/{pk}/deactivate/")
        self.assertEqual(deactivate.status_code, 200)
        self.assertFalse(DailyReceipt.objects.get(pk=pk).is_active)

    def test_bulk_saves_only_active_heads(self):
        inactive = ReceiptHead.objects.create(
            code="OLD", description="Inactive", is_active=False
        )
        bank = ReceiptHead.objects.create(code="BANK", description="Bank")
        response = self.client.post(
            "/api/receipts/bulk/",
            {
                "institution": self.inst.id,
                "business_date": "2026-08-17",
                "lines": [
                    {"receipt_head": self.head.id, "amount": "1000.00"},
                    {"receipt_head": bank.id, "amount": "2500.50"},
                    {"receipt_head": inactive.id, "amount": "999.00"},
                    {"receipt_head": self.head.id, "amount": ""},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DailyReceipt.objects.filter(is_active=True).count(), 2)
        self.assertFalse(
            DailyReceipt.objects.filter(receipt_head=inactive).exists()
        )

    def test_entry_sheet_lists_only_active_heads(self):
        ReceiptHead.objects.create(code="OLD", description="Inactive", is_active=False)
        ReceiptHead.objects.create(code="BANK", description="Bank")
        response = self.client.get(
            "/api/receipts/entry-sheet/",
            {"business_date": "2026-08-17", "institution_id": self.inst.id},
        )
        self.assertEqual(response.status_code, 200)
        codes = [row["code"] for row in response.data["rows"]]
        self.assertEqual(codes, ["BANK", "CASH"])
        self.assertNotIn("OLD", codes)
