from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum

from partners.models import PartnerGroupEntry

SHARE_LIMIT = Decimal("100")


def _pk(value):
    if value is None:
        return None
    return value.pk if hasattr(value, "pk") else int(value)


def active_share_sum(partner_group_id, institution_id, exclude_pk=None) -> Decimal:
    qs = PartnerGroupEntry.objects.filter(
        partner_group_id=partner_group_id,
        institution_id=institution_id,
        is_active=True,
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    total = qs.aggregate(total=Sum("share_percent"))["total"]
    return total or Decimal("0")


def validate_group_institution_share_limit(
    partner_group_id,
    institution_id,
    share_percent,
    *,
    exclude_pk=None,
    is_active=True,
):
    """Active partners' share % for one group + institution cannot exceed 100."""
    if not is_active or share_percent is None:
        return Decimal("0")
    group_id = _pk(partner_group_id)
    inst_id = _pk(institution_id)
    if group_id is None or inst_id is None:
        return Decimal("0")
    others = active_share_sum(group_id, inst_id, exclude_pk=exclude_pk)
    total = others + Decimal(share_percent)
    if total > SHARE_LIMIT:
        raise ValidationError(
            {
                "share_percent": (
                    "Active partners' share percent for this group and institution cannot exceed 100%. "
                    f"Other active shares total {others}%, this entry would make {total}%."
                )
            }
        )
    return total


def validate_institution_single_group(institution_id, partner_group_id, *, exclude_pk=None):
    """Each institution may be assigned only one partner group."""
    inst_id = _pk(institution_id)
    group_id = _pk(partner_group_id)
    if inst_id is None or group_id is None:
        return
    qs = PartnerGroupEntry.objects.filter(institution_id=inst_id)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    existing_ids = set(qs.values_list("partner_group_id", flat=True))
    if existing_ids - {group_id}:
        raise ValidationError(
            {
                "partner_group": (
                    "Each institution can have only one partner group. "
                    "This institution is already assigned to another group."
                )
            }
        )


def validate_partner_once_per_institution(institution_id, partner_id, *, exclude_pk=None):
    """A partner may join many groups, but only once per institution."""
    inst_id = _pk(institution_id)
    partner_pk = _pk(partner_id)
    if inst_id is None or partner_pk is None:
        return
    qs = PartnerGroupEntry.objects.filter(institution_id=inst_id, partner_id=partner_pk)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ValidationError(
            {
                "partner": (
                    "This partner is already in this institution's group. "
                    "The same partner can still be added to other groups at other institutions."
                )
            }
        )
