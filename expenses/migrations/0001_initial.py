import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("institutions", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ExpenseHead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=30, unique=True)),
                ("description", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
            ],
            options={
                "verbose_name": "Expense Head",
                "verbose_name_plural": "Expense Heads",
                "db_table": "expense_heads",
                "ordering": ["code"],
            },
        ),
        migrations.CreateModel(
            name="DailyExpense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entry_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=18,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                ("business_date", models.DateField(db_index=True)),
                ("transaction_date", models.DateTimeField(auto_now_add=True)),
                (
                    "entered_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_entered",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "institution",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="daily_expenses",
                        to="institutions.institution",
                    ),
                ),
                (
                    "modified_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_modified",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "expense_head",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="daily_expenses",
                        to="expenses.expensehead",
                    ),
                ),
            ],
            options={
                "db_table": "daily_expenses",
                "ordering": ["-business_date", "-id"],
                "indexes": [
                    models.Index(fields=["institution", "business_date"], name="daily_expen_institu_idx"),
                    models.Index(fields=["business_date"], name="daily_expen_busines_idx"),
                    models.Index(fields=["transaction_date"], name="daily_expen_transac_idx"),
                    models.Index(fields=["expense_head"], name="daily_expen_expense_idx"),
                    models.Index(fields=["institution", "is_active", "business_date"], name="daily_expen_inst_act_idx"),
                ],
            },
        ),
    ]
