from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from institutions.models import Institution


class Partner(models.Model):
    """Legacy table: PARTNERS. Organization-wide partner master."""

    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "partners"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PartnerGroup(models.Model):
    """
    Legacy table: PARTNER_GROUP.

    Original column WTSAPPGROUP is mapped to whatsapp_group
    (db_column remains wtsappgroup for possible legacy dumps).
    """

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)
    whatsapp_group = models.CharField(
        max_length=255,
        blank=True,
        db_column="wtsappgroup",
    )
    is_profit_sharing = models.BooleanField(
        default=False,
        help_text="When true, this group is used for monthly partner wage calculation.",
    )

    class Meta:
        db_table = "partner_group"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PartnerGroupEntry(models.Model):
    """Legacy table: PARTNER_GROUP_ENTRIES. Share percent is per institution."""

    partner_group = models.ForeignKey(
        PartnerGroup,
        on_delete=models.PROTECT,
        related_name="entries",
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="partner_group_entries",
    )
    partner = models.ForeignKey(
        Partner,
        on_delete=models.PROTECT,
        related_name="group_entries",
    )
    share_percent = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "partner_group_entries"
        constraints = [
            models.UniqueConstraint(
                fields=["partner_group", "institution", "partner"],
                name="uniq_group_institution_partner",
            ),
        ]
        indexes = [
            models.Index(fields=["institution", "partner_group", "is_active"]),
            models.Index(fields=["partner"]),
        ]

    def __str__(self) -> str:
        return f"{self.partner} @ {self.institution} ({self.share_percent}%)"

    def clean(self):
        if self.share_percent is not None and not (
            Decimal("0") <= self.share_percent <= Decimal("100")
        ):
            raise ValidationError({"share_percent": "Share percent must be between 0 and 100."})
