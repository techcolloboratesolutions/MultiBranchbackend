from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from partners.models import PartnerGroupEntry
from reports.services import period_totals
from wages.models import BusinessWage
from core.money import HUNDRED, calculate_partner_wage, money


def profit_share_entries(institution_id):
    """Partners in this institution's single group, when that group is profit-sharing."""
    group_ids = list(
        PartnerGroupEntry.objects.filter(institution_id=institution_id)
        .values_list("partner_group_id", flat=True)
        .distinct()
    )
    if len(group_ids) > 1:
        raise ValidationError("Each institution can have only one partner group.")
    if not group_ids:
        return PartnerGroupEntry.objects.none()
    return (
        PartnerGroupEntry.objects.select_related("partner", "partner_group")
        .filter(
            institution_id=institution_id,
            partner_group_id=group_ids[0],
            is_active=True,
            partner_group__is_profit_sharing=True,
            partner_group__is_active=True,
            partner__is_active=True,
        )
        .order_by("partner__name", "id")
    )


def validate_share_total(entries):
    total = sum((entry.share_percent for entry in entries), Decimal("0"))
    if total > HUNDRED:
        raise ValidationError(
            f"Active share percent for this group and institution cannot exceed 100%. Current total is {total}."
        )
    if money(total) != money(HUNDRED):
        raise ValidationError(
            f"Active profit-sharing percentages for this group and institution must total 100%. Current total is {total}."
        )
    return total


def preview_wages(institution_id, year: int, month: int):
    totals = period_totals(institution_id, year, month)
    entries = list(profit_share_entries(institution_id))
    share_total = sum((entry.share_percent for entry in entries), Decimal("0"))
    partners = []
    seen = set()
    for entry in entries:
        if entry.partner_id in seen:
            continue
        seen.add(entry.partner_id)
        wage = calculate_partner_wage(totals["total_balance"], entry.share_percent)
        partners.append(
            {
                "partner_id": entry.partner_id,
                "partner_name": entry.partner.name,
                "group_name": entry.partner_group.name,
                "share_percent": entry.share_percent,
                "partner_wage_amount": wage,
                "partner_mobile": entry.partner.mobile or "",
            }
        )
    return {
        "institution_id": institution_id,
        "year": year,
        "month": month,
        "total_sales": totals["total_receipt"],
        "total_purchase": totals["total_payment"],
        "total_expense": totals["total_expense"],
        "total_business": totals["total_business"],
        "total_balance": totals["total_balance"],
        "share_total": share_total,
        "group_name": entries[0].partner_group.name if entries else "",
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
                "total_sales": preview["total_sales"],
                "total_purchase": preview["total_purchase"],
                "total_business": preview["total_business"],
                "total_expense": preview["total_expense"],
                "total_balance": preview["total_balance"],
                "business_percent": row["share_percent"],
                "partner_wage_amount": row["partner_wage_amount"],
                "entered_by": user,
                "modified_by": user,
                "is_active": True,
            },
        )
        saved.append(obj)
    return preview, saved
