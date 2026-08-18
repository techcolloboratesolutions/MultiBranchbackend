from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from partners.models import PartnerGroupEntry
from reports.services import period_totals
from wages.models import BusinessWage
from core.money import HUNDRED, calculate_partner_wage, money


def profit_share_entries(institution_id):
    return PartnerGroupEntry.objects.select_related("partner", "partner_group").filter(
        institution_id=institution_id,
        is_active=True,
        partner_group__is_profit_sharing=True,
        partner_group__is_active=True,
        partner__is_active=True,
    )


def validate_share_total(entries):
    total = sum((entry.share_percent for entry in entries), Decimal("0"))
    if money(total) != money(HUNDRED):
        raise ValidationError(
            f"Active profit-sharing percentages must total 100%. Current total is {total}."
        )
    return total


def preview_wages(institution_id, year: int, month: int):
    totals = period_totals(institution_id, year, month)
    entries = list(profit_share_entries(institution_id))
    share_total = sum((entry.share_percent for entry in entries), Decimal("0"))
    partners = []
    for entry in entries:
        wage = calculate_partner_wage(totals["total_business"], entry.share_percent)
        partners.append(
            {
                "partner_id": entry.partner_id,
                "partner_name": entry.partner.name,
                "share_percent": entry.share_percent,
                "partner_wage_amount": wage,
            }
        )
    return {
        "institution_id": institution_id,
        "year": year,
        "month": month,
        "total_receipt": totals["total_receipt"],
        "total_payment": totals["total_payment"],
        "total_business": totals["total_business"],
        "share_total": share_total,
        "partners": partners,
    }


@transaction.atomic
def save_wages(institution, year: int, month: int, user):
    preview = preview_wages(institution.id, year, month)
    entries = list(profit_share_entries(institution.id))
    validate_share_total(entries)
    saved = []
    for row in preview["partners"]:
        obj, _created = BusinessWage.objects.update_or_create(
            institution=institution,
            partner_id=row["partner_id"],
            wages_year=year,
            wages_month=month,
            defaults={
                "total_receipt": preview["total_receipt"],
                "total_payment": preview["total_payment"],
                "total_business": preview["total_business"],
                "business_percent": row["share_percent"],
                "partner_wage_amount": row["partner_wage_amount"],
                "entered_by": user,
                "modified_by": user,
                "is_active": True,
            },
        )
        saved.append(obj)
    return preview, saved
