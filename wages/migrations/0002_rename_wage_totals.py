from decimal import Decimal

from django.db import migrations, models


def backfill_balance(apps, schema_editor):
    BusinessWage = apps.get_model("wages", "BusinessWage")
    for row in BusinessWage.objects.all().iterator():
        expense = row.total_expense or Decimal("0.00")
        row.total_balance = (row.total_sales or Decimal("0.00")) - expense
        row.total_business = (row.total_sales or Decimal("0.00")) + (row.total_purchase or Decimal("0.00"))
        row.save(update_fields=["total_balance", "total_business"])


class Migration(migrations.Migration):

    dependencies = [
        ("wages", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="businesswage",
            old_name="total_receipt",
            new_name="total_sales",
        ),
        migrations.RenameField(
            model_name="businesswage",
            old_name="total_payment",
            new_name="total_purchase",
        ),
        migrations.AddField(
            model_name="businesswage",
            name="total_expense",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=18),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="businesswage",
            name="total_balance",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=18),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_balance, migrations.RunPython.noop),
    ]
