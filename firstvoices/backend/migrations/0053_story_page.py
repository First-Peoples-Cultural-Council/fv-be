# Generated by Django 4.2.3 on 2023-07-21 05:04

import backend.permissions.managers
from django.conf import settings
import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import rules.contrib.models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0052_alter_dictionaryentry_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="Story",
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
                    "visibility",
                    models.IntegerField(
                        choices=[(0, "Team"), (10, "Members"), (20, "Public")],
                        default=0,
                    ),
                ),
                ("exclude_from_games", models.BooleanField(default=False)),
                ("exclude_from_kids", models.BooleanField(default=False)),
                ("title", models.CharField()),
                ("title_translation", models.CharField(blank=True)),
                ("introduction", models.CharField(blank=True)),
                ("introduction_translation", models.CharField(blank=True)),
                (
                    "acknowledgements",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.TextField(max_length=1000),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "notes",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.TextField(max_length=1000),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "cover_image",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="story_cover_of",
                        to="backend.image",
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
                    "last_modified_by",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="modified_%(app_label)s_%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "related_audio",
                    models.ManyToManyField(blank=True, to="backend.audio"),
                ),
                (
                    "related_images",
                    models.ManyToManyField(blank=True, to="backend.image"),
                ),
                (
                    "related_videos",
                    models.ManyToManyField(blank=True, to="backend.video"),
                ),
                (
                    "site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s_set",
                        to="backend.site",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "stories",
                "unique_together": {("site", "title")},
            },
            bases=(
                backend.permissions.managers.PermissionFilterMixin,
                rules.contrib.models.RulesModelMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="Page",
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
                    "ordering",
                    models.SmallIntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("text", models.TextField(max_length=1000)),
                ("translation", models.TextField(blank=True, max_length=1000)),
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
                (
                    "related_audio",
                    models.ManyToManyField(blank=True, to="backend.audio"),
                ),
                (
                    "related_images",
                    models.ManyToManyField(blank=True, to="backend.image"),
                ),
                (
                    "related_videos",
                    models.ManyToManyField(blank=True, to="backend.video"),
                ),
                (
                    "story",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pages",
                        to="backend.story",
                    ),
                ),
            ],
            options={
                "ordering": ("ordering",),
                "unique_together": {("story", "ordering")},
            },
            bases=(
                backend.permissions.managers.PermissionFilterMixin,
                rules.contrib.models.RulesModelMixin,
                models.Model,
            ),
        ),
    ]
