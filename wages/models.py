from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import AuditMixin
from institutions.models import Institution
from partners.models import Partner


class BusinessWage(AuditMixin):
    """
    Legacy table: BUSINESS_WAGES.

    Totals are a confirmed snapshot. On save they are recalculated from
    period sales, purchases, and expenses. total_business = sales + purchase;
    total_balance = sales - expense.
    """

    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="business_wages",
        db_column="for_inst_id",
    )
    wages_month = models.PositiveSmallIntegerField()
    wages_year = models.PositiveSmallIntegerField()
    total_sales = models.DecimalField(max_digits=18, decimal_places=2)
    total_purchase = models.DecimalField(max_digits=18, decimal_places=2)
    total_business = models.DecimalField(max_digits=18, decimal_places=2)
    total_expense = models.DecimalField(max_digits=18, decimal_places=2)
    total_balance = models.DecimalField(max_digits=18, decimal_places=2)
    business_percent = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        help_text="Partner share percent at the time of confirmation.",
    )
    partner = models.ForeignKey(
        Partner,
        on_delete=models.PROTECT,
        related_name="business_wages",
    )
    partner_wage_amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        db_table = "business_wages"
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "partner", "wages_year", "wages_month"],
                name="uniq_wage_institution_partner_period",
            ),
            models.CheckConstraint(
                condition=models.Q(wages_month__gte=1) & models.Q(wages_month__lte=12),
                name="chk_wages_month_range",
            ),
        ]
        indexes = [
            models.Index(fields=["institution", "wages_year", "wages_month"]),
            models.Index(fields=["partner"]),
        ]

    def __str__(self) -> str:
        return f"{self.institution_id} {self.wages_year}-{self.wages_month:02d} {self.partner_id}"
