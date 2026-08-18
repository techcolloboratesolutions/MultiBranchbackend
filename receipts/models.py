from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.models import AuditMixin
from institutions.models import Institution


class ReceiptHead(models.Model):
    """Legacy table: RECEIPT_HEADS. Global catalog (not per branch)."""

    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "receipt_heads"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.description}"


class DailyReceipt(AuditMixin):
    """Legacy table: DAILY_RECEIPTS. Soft-deactivate instead of deleting."""

    receipt_head = models.ForeignKey(
        ReceiptHead,
        on_delete=models.PROTECT,
        related_name="daily_receipts",
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
        related_name="daily_receipts",
    )

    class Meta:
        db_table = "daily_receipts"
        indexes = [
            models.Index(fields=["institution", "business_date"]),
            models.Index(fields=["business_date"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["receipt_head"]),
            models.Index(fields=["institution", "is_active", "business_date"]),
        ]
        ordering = ["-business_date", "-id"]

    def __str__(self) -> str:
        return f"{self.institution_id} {self.business_date} {self.amount}"
