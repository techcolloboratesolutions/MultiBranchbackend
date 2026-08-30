from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role, User
from institutions.models import Institution, MainInstitution
from partners.models import Partner, PartnerGroup, PartnerGroupEntry
from expenses.models import ExpenseHead
from payments.models import PaymentHead
from receipts.models import ReceiptHead

ADMIN_PASSWORD = "ChangeMeAdmin123!"
MANAGER_PASSWORD = "ChangeMeManager123!"

BRANCHES = [
    ("Head Office", "Mumbai"),
    ("Andheri Branch", "Mumbai"),
    ("Pune Branch", "Pune"),
    ("Nagpur Branch", "Nagpur"),
    ("Nashik Branch", "Nashik"),
    ("Delhi Branch", "New Delhi"),
    ("Noida Branch", "Noida"),
    ("Jaipur Branch", "Jaipur"),
    ("Ahmedabad Branch", "Ahmedabad"),
    ("Surat Branch", "Surat"),
    ("Bengaluru Branch", "Bengaluru"),
    ("Chennai Branch", "Chennai"),
    ("Hyderabad Branch", "Hyderabad"),
    ("Kolkata Branch", "Kolkata"),
    ("Kochi Branch", "Kochi"),
]

RECEIPT_HEADS = [
    ("CASH", "Cash Collection"),
    ("BANK", "Bank Deposit"),
    ("FEE", "Fee Collection"),
    ("GRANT", "Grants"),
    ("OTHER", "Other Receipts"),
]

EXPENSE_HEADS = [
    ("STAFF", "Staff Expenses"),
    ("TRAVEL", "Travel"),
    ("OFFICE", "Office Supplies"),
    ("MISC", "Miscellaneous"),
]

PAYMENT_HEADS = [
    ("SAL", "Salaries", "Monthly"),
    ("RENT", "Rent", "Monthly"),
    ("UTIL", "Utilities", "Daily"),
    ("VEND", "Vendor Payments", "Daily"),
    ("MAIN", "Maintenance", "Daily"),
    ("OTHER", "Other Payments", "Daily"),
]

PARTNERS = [
    ("Partner A", "9000000001", "partner.a@example.com", Decimal("40.0000")),
    ("Partner B", "9000000002", "partner.b@example.com", Decimal("35.0000")),
    ("Partner C", "9000000003", "partner.c@example.com", Decimal("25.0000")),
]


class Command(BaseCommand):
    help = "Idempotent seed: 1 main org, 15 branches, admin, 15 managers, catalogs, partners."

    @transaction.atomic
    def handle(self, *args, **options):
        main, _ = MainInstitution.objects.get_or_create(
            name="Horizon Group",
            defaults={
                "place": "Mumbai",
                "address": "Nariman Point, Mumbai",
                "legal_name": "Horizon Group Private Limited",
                "country": "India",
                "state": "Maharashtra",
                "city": "Mumbai",
                "district": "Mumbai",
                "email": "admin@horizongroup.example",
                "phone": "02200000000",
                "is_active": True,
            },
        )

        institutions = []
        for name, city in BRANCHES:
            inst, _ = Institution.objects.get_or_create(
                name=name,
                main_institution=main,
                defaults={
                    "city": city,
                    "country": "India",
                    "state": "Maharashtra" if city in {"Mumbai", "Pune", "Nagpur", "Nashik"} else "",
                    "contact_person": f"Manager - {name}",
                    "is_active": True,
                },
            )
            institutions.append(inst)

        admin_role, _ = Role.objects.get_or_create(
            role_code=Role.Code.ADMIN,
            institution=None,
            defaults={"role_description": "Organization administrator", "is_active": True},
        )
        manager_role, _ = Role.objects.get_or_create(
            role_code=Role.Code.MANAGER,
            institution=None,
            defaults={"role_description": "Branch manager", "is_active": True},
        )

        head_office = institutions[0]
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "full_name": "System Administrator",
                "email": "admin@horizongroup.example",
                "institution": head_office,
                "role": admin_role,
                "is_staff": True,
                "is_superuser": True,
                "status": User.Status.ACTIVE,
            },
        )
        if created:
            admin.set_password(ADMIN_PASSWORD)
            admin.save()

        for index, inst in enumerate(institutions, start=1):
            username = f"manager{index:02d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "full_name": f"Manager {index:02d} - {inst.name}",
                    "email": f"{username}@horizongroup.example",
                    "institution": inst,
                    "role": manager_role,
                    "status": User.Status.ACTIVE,
                },
            )
            if created:
                user.set_password(MANAGER_PASSWORD)
                user.save()

        for code, desc in RECEIPT_HEADS:
            ReceiptHead.objects.get_or_create(
                code=code,
                defaults={"description": desc, "is_active": True},
            )

        for code, desc in EXPENSE_HEADS:
            ExpenseHead.objects.get_or_create(
                code=code,
                defaults={"description": desc, "is_active": True},
            )

        for code, desc, recurring_type in PAYMENT_HEADS:
            PaymentHead.objects.get_or_create(
                code=code,
                defaults={
                    "description": desc,
                    "is_active": True,
                    "recurring_type": recurring_type,
                },
            )

        group, _ = PartnerGroup.objects.get_or_create(
            name="Profit Sharing",
            defaults={
                "is_active": True,
                "is_profit_sharing": True,
                "whatsapp_group": "Horizon Partners",
            },
        )
        if not group.is_profit_sharing:
            group.is_profit_sharing = True
            group.save(update_fields=["is_profit_sharing"])

        partner_rows = []
        for name, mobile, email, share in PARTNERS:
            partner, _ = Partner.objects.get_or_create(
                name=name,
                defaults={"mobile": mobile, "email": email, "is_active": True},
            )
            partner_rows.append((partner, share))

        for inst in institutions:
            for partner, share in partner_rows:
                PartnerGroupEntry.objects.get_or_create(
                    partner_group=group,
                    institution=inst,
                    partner=partner,
                    defaults={"share_percent": share, "is_active": True},
                )

        self.stdout.write(self.style.SUCCESS("Seed data applied."))
        self.stdout.write(f"Main institution: {main.name} (id={main.id})")
        self.stdout.write(f"Institutions: {len(institutions)}")
        self.stdout.write("Dev logins (hashed in DB, change before sharing):")
        self.stdout.write(f"  admin / {ADMIN_PASSWORD}")
        self.stdout.write(f"  manager01..manager15 / {MANAGER_PASSWORD}")
