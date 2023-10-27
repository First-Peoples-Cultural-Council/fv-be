# Generated by Django 4.2.6 on 2023-10-26 18:24

import backend.permissions.managers
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import rules.contrib.models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("backend", "0078_rename_contact_email_site_contact_emails"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="joinrequest",
            name="reason",
        ),
        migrations.CreateModel(
            name="JoinRequestReason",
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
                (
                    "created",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now
                    ),
                ),
                (
                    "last_modified",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now
                    ),
                ),
                (
                    "reason",
                    models.IntegerField(
                        choices=[
                            (10, "Other"),
                            (20, "Learning the language"),
                            (30, "Teaching the language"),
                            (40, "Fluent speaker"),
                            (50, "Interested in languages"),
                            (60, "Part of my heritage"),
                            (70, "Member of this community/nation"),
                            (80, "Working with this community/nation"),
                            (90, "Reconciliation"),
                            (100, "Part of this FirstVoices Language Team"),
                        ],
                        default=10,
                    ),
                ),
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
                    "join_request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reasons_set",
                        to="backend.joinrequest",
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
                "verbose_name": "Join Request Reason",
                "verbose_name_plural": "Join Request Reasons",
            },
            bases=(
                backend.permissions.managers.PermissionFilterMixin,
                rules.contrib.models.RulesModelMixin,
                models.Model,
            ),
        ),
    ]
