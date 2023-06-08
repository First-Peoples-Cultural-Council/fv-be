# Generated by Django 4.2.2 on 2023-06-07 18:56

import backend.permissions.managers
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import rules.contrib.models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0031_merge_20230605_1003"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppImportStatus",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("last_modified", models.DateTimeField(auto_now=True, db_index=True)),
                ("label", models.CharField(max_length=150)),
                ("successful", models.BooleanField(default=False)),
                ("no_warnings", models.BooleanField(default=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_%(app_label)s_%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "last_modified_by",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="modified_%(app_label)s_%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "import status",
                "verbose_name_plural": "import statuses",
            },
            bases=(
                backend.permissions.managers.PermissionFilterMixin,
                rules.contrib.models.RulesModelMixin,
                models.Model,
            ),
        ),
    ]
