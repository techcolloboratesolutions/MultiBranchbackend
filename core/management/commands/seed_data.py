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
CHIEF_PASSWORD = "ChangeMeChief123!"

BRANCHES = [
    ("Head Office", "Mumbai", "Maharashtra"),
    ("Andheri Branch", "Mumbai", "Maharashtra"),
    ("Pune Branch", "Pune", "Maharashtra"),
    ("Nagpur Branch", "Nagpur", "Maharashtra"),
    ("Nashik Branch", "Nashik", "Maharashtra"),
    ("Delhi Branch", "New Delhi", "Delhi"),
    ("Noida Branch", "Noida", "Uttar Pradesh"),
    ("Jaipur Branch", "Jaipur", "Rajasthan"),
    ("Ahmedabad Branch", "Ahmedabad", "Gujarat"),
    ("Surat Branch", "Surat", "Gujarat"),
    ("Bengaluru Branch", "Bengaluru", "Karnataka"),
    ("Chennai Branch", "Chennai", "Tamil Nadu"),
    ("Hyderabad Branch", "Hyderabad", "Telangana"),
    ("Kolkata Branch", "Kolkata", "West Bengal"),
    ("Kochi Branch", "Kochi", "Kerala"),
]

# Horizon keeps the original branch names and manager01–manager15.
# The two added groups prefix branch names so they stay distinct in the lists.
ORGANIZATIONS = [
    {
        "name": "Horizon Group",
        "legal_name": "Horizon Group Private Limited",
        "place": "Mumbai",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Nariman Point, Mumbai",
        "email": "admin@horizongroup.example",
        "phone": "02200000000",
        "branch_prefix": "",
        "chief_username": "chief",
        "manager_start": 1,
    },
    {
        "name": "Western Bay Group",
        "legal_name": "Western Bay Group Private Limited",
        "place": "Ahmedabad",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "CG Road, Ahmedabad",
        "email": "admin@westernbay.example",
        "phone": "07900000000",
        "branch_prefix": "West ",
        "chief_username": "chief2",
        "manager_start": 16,
    },
    {
        "name": "Eastern Bay Group",
        "legal_name": "Eastern Bay Group Private Limited",
        "place": "Kolkata",
        "city": "Kolkata",
        "state": "West Bengal",
        "address": "Park Street, Kolkata",
        "email": "admin@easternbay.example",
        "phone": "03300000000",
        "branch_prefix": "East ",
        "chief_username": "chief3",
        "manager_start": 31,
    },
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


def _ensure_user(username, password, **defaults):
    user, created = User.objects.get_or_create(username=username, defaults=defaults)
    if created:
        user.set_password(password)
        user.save()
    return user


class Command(BaseCommand):
    help = "Idempotent seed: 3 main institutions, 15 branches each, admin, chief per main, manager per branch."

    @transaction.atomic
    def handle(self, *args, **options):
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
        chief_role, _ = Role.objects.get_or_create(
            role_code=Role.Code.CHIEF_MANAGER,
            institution=None,
            defaults={"role_description": "Chief Manager", "is_active": True},
        )

        all_institutions = []
        org_summaries = []
        for org in ORGANIZATIONS:
            main, _ = MainInstitution.objects.get_or_create(
                name=org["name"],
                defaults={
                    "place": org["place"],
                    "address": org["address"],
                    "legal_name": org["legal_name"],
                    "country": "India",
                    "state": org["state"],
                    "city": org["city"],
                    "district": org["city"],
                    "email": org["email"],
                    "phone": org["phone"],
                    "is_active": True,
                },
            )
            institutions = []
            for branch_name, city, state in BRANCHES:
                name = f"{org['branch_prefix']}{branch_name}"
                inst, _ = Institution.objects.get_or_create(
                    name=name,
                    main_institution=main,
                    defaults={
                        "city": city,
                        "country": "India",
                        "state": state,
                        "contact_person": f"Manager - {name}",
                        "is_active": True,
                    },
                )
                institutions.append(inst)
            all_institutions.extend(institutions)

            head_office = institutions[0]
            chief = _ensure_user(
                org["chief_username"],
                CHIEF_PASSWORD,
                full_name=f"Chief Manager - {main.name}",
                email=f"{org['chief_username']}@{org['email'].split('@', 1)[1]}",
                institution=head_office,
                role=chief_role,
                status=User.Status.ACTIVE,
            )
            if chief.institution_id != head_office.id or chief.role_id != chief_role.id:
                chief.institution = head_office
                chief.role = chief_role
                chief.save(update_fields=["institution", "role"])

            manager_names = []
            for offset, inst in enumerate(institutions):
                index = org["manager_start"] + offset
                username = f"manager{index:02d}"
                manager_names.append(username)
                user = _ensure_user(
                    username,
                    MANAGER_PASSWORD,
                    full_name=f"Manager {index:02d} - {inst.name}",
                    email=f"{username}@{org['email'].split('@', 1)[1]}",
                    institution=inst,
                    role=manager_role,
                    status=User.Status.ACTIVE,
                )
                if user.institution_id != inst.id or user.role_id != manager_role.id:
                    user.institution = inst
                    user.role = manager_role
                    user.save(update_fields=["institution", "role"])

            org_summaries.append((main, head_office, org["chief_username"], manager_names[0], manager_names[-1]))

        horizon_head = all_institutions[0]
        _ensure_user(
            "admin",
            ADMIN_PASSWORD,
            full_name="System Administrator",
            email="admin@horizongroup.example",
            institution=horizon_head,
            role=admin_role,
            is_staff=True,
            is_superuser=True,
            status=User.Status.ACTIVE,
        )

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

        for inst in all_institutions:
            for partner, share in partner_rows:
                PartnerGroupEntry.objects.get_or_create(
                    partner_group=group,
                    institution=inst,
                    partner=partner,
                    defaults={"share_percent": share, "is_active": True},
                )

        self.stdout.write(self.style.SUCCESS("Seed data applied."))
        self.stdout.write(f"Main institutions: {len(org_summaries)}")
        self.stdout.write(f"Institutions: {len(all_institutions)}")
        self.stdout.write("Dev logins (hashed in DB, change before sharing):")
        self.stdout.write(f"  admin / {ADMIN_PASSWORD}  (all main institutions)")
        for main, head, chief_username, first_manager, last_manager in org_summaries:
            self.stdout.write(
                f"  {main.name}: {chief_username} / {CHIEF_PASSWORD} on {head.name}; "
                f"{first_manager}..{last_manager} / {MANAGER_PASSWORD}"
            )
