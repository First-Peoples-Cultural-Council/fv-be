# Generated by Django 4.2.7 on 2023-12-07 19:11

import backend.permissions.managers
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import rules.contrib.models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("backend", "0084_language_community_keywords_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Gallery",
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
                ("title", models.CharField(max_length=225)),
                ("title_translation", models.CharField(blank=True, max_length=225)),
                ("introduction", models.TextField(blank=True)),
                ("introduction_translation", models.TextField(blank=True)),
                (
                    "cover_image",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="gallery_cover_image",
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
                    "site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s_set",
                        to="backend.site",
                    ),
                ),
            ],
            options={
                "verbose_name": "gallery",
                "verbose_name_plural": "galleries",
            },
            bases=(
                backend.permissions.managers.PermissionFilterMixin,
                rules.contrib.models.RulesModelMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="GalleryItem",
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
                    "order",
                    models.SmallIntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
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
                    "gallery",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="backend.gallery",
                    ),
                ),
                (
                    "image",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gallery_images",
                        to="backend.image",
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
                "verbose_name": "gallery item",
                "verbose_name_plural": "gallery items",
                "indexes": [
                    models.Index(
                        fields=["gallery", "order"], name="gallery_item_order_idx"
                    )
                ],
            },
            bases=(
                backend.permissions.managers.PermissionFilterMixin,
                rules.contrib.models.RulesModelMixin,
                models.Model,
            ),
        ),
        migrations.AddConstraint(
            model_name="galleryitem",
            constraint=models.UniqueConstraint(
                fields=("gallery", "image"), name="unique_gallery_image"
            ),
        ),
        migrations.AddConstraint(
            model_name="galleryitem",
            constraint=models.UniqueConstraint(
                fields=("gallery", "order"), name="unique_gallery_item_order"
            ),
        ),
    ]
