from django.db import migrations


def create_chief_manager_role(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.get_or_create(
        role_code="CHIEF_MANAGER",
        institution=None,
        defaults={
            "role_description": "Chief Manager",
            "is_active": True,
        },
    )


def remove_chief_manager_role(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(role_code="CHIEF_MANAGER", institution__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_chief_manager_role, remove_chief_manager_role),
    ]
