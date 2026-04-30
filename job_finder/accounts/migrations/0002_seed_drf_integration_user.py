import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_integration_user(apps, schema_editor):
    User = apps.get_model("accounts", "CustomUser")
    DRF = os.environ.get("DRF")
    if not DRF or DRF == "":
        raise EnvironmentError("Missing DRF auth credentials")

    username = DRF.split(":")[0]
    password = DRF.split(":")[1]
    email = username

    if username and password:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "password": make_password(password),
                "is_active": True,
            },
        )
        if not created:
            user.password = make_password(password)
            user.save(update_fields=["password"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(create_integration_user, migrations.RunPython.noop),
    ]
