from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.models import AuditMixin
from institutions.models import Institution


class ExpenseHead(models.Model):
    """Legacy table: EXPENSE_HEADS. Global catalog (not per branch)."""

    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "expense_heads"
        ordering = ["code"]
        verbose_name = "Expense Head"
        verbose_name_plural = "Expense Heads"

    def __str__(self) -> str:
        return f"{self.code} - {self.description}"


class DailyExpense(AuditMixin):
    """Legacy table: Daily_Expenses. Soft-deactivate instead of deleting."""

    expense_head = models.ForeignKey(
        ExpenseHead,
        on_delete=models.PROTECT,
        related_name="daily_expenses",
    )
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    business_date = models.DateField(db_index=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="daily_expenses",
    )

    class Meta:
        db_table = "daily_expenses"
        indexes = [
            models.Index(fields=["institution", "business_date"]),
            models.Index(fields=["business_date"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["expense_head"]),
            models.Index(fields=["institution", "is_active", "business_date"]),
        ]
        ordering = ["-business_date", "-id"]

    def __str__(self) -> str:
        return f"{self.institution_id} {self.business_date} {self.amount}"
