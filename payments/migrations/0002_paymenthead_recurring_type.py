from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymenthead",
            name="recurring_type",
            field=models.CharField(
                choices=[("Daily", "Daily"), ("Monthly", "Monthly")],
                db_index=True,
                default="Daily",
                max_length=20,
            ),
        ),
    ]
