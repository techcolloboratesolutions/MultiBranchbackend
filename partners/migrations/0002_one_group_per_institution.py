from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("partners", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="partnergroupentry",
            constraint=models.UniqueConstraint(
                fields=("institution", "partner"),
                name="uniq_institution_partner",
            ),
        ),
    ]
