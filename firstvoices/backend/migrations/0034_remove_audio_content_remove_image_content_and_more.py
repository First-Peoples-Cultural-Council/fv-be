# Generated by Django 4.2.2 on 2023-06-14 22:13

import backend.models.media
import backend.permissions.managers
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import rules.contrib.models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0033_embeddedvideo"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="audio",
            name="content",
        ),
        migrations.RemoveField(
            model_name="image",
            name="content",
        ),
        migrations.RemoveField(
            model_name="image",
            name="medium",
        ),
        migrations.RemoveField(
            model_name="image",
            name="small",
        ),
        migrations.RemoveField(
            model_name="image",
            name="thumbnail",
        ),
        migrations.RemoveField(
            model_name="video",
            name="content",
        ),
        migrations.AlterField(
            model_name="person",
            name="bio",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.CreateModel(
            name="VideoFile",
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
                (
                    "content",
                    models.FileField(
                        upload_to=backend.models.media.media_directory_path
                    ),
                ),
                ("mimetype", models.CharField(blank=True, null=True)),
                ("height", models.IntegerField(blank=True, null=True)),
                ("width", models.IntegerField(blank=True, null=True)),
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
                "verbose_name": "Video File",
                "verbose_name_plural": "Video Files",
            },
            bases=(
                backend.permissions.managers.PermissionFilterMixin,
                rules.contrib.models.RulesModelMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="ImageFile",
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
                ("mimetype", models.CharField(blank=True, null=True)),
                ("height", models.IntegerField(blank=True, null=True)),
                ("width", models.IntegerField(blank=True, null=True)),
                (
                    "content",
                    models.ImageField(
                        height_field="height",
                        upload_to=backend.models.media.media_directory_path,
                        width_field="width",
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
                "verbose_name": "Image File",
                "verbose_name_plural": "Image Files",
            },
            bases=(
                backend.permissions.managers.PermissionFilterMixin,
                rules.contrib.models.RulesModelMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="File",
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
                (
                    "content",
                    models.FileField(
                        upload_to=backend.models.media.media_directory_path
                    ),
                ),
                ("mimetype", models.CharField(blank=True, null=True)),
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
                "verbose_name": "File",
                "verbose_name_plural": "Files",
            },
            bases=(
                backend.permissions.managers.PermissionFilterMixin,
                rules.contrib.models.RulesModelMixin,
                models.Model,
            ),
        ),
        migrations.AddField(
            model_name="audio",
            name="original",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="backend.file",
            ),
        ),
        migrations.AddField(
            model_name="embeddedvideo",
            name="original",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="backend.file",
            ),
        ),
        migrations.AddField(
            model_name="image",
            name="medium_id",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="image_medium",
                to="backend.imagefile",
            ),
        ),
        migrations.AddField(
            model_name="image",
            name="original",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="image",
                to="backend.imagefile",
            ),
        ),
        migrations.AddField(
            model_name="image",
            name="small_id",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="image_small",
                to="backend.imagefile",
            ),
        ),
        migrations.AddField(
            model_name="image",
            name="thumbnail_id",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="image_thumbnail",
                to="backend.imagefile",
            ),
        ),
        migrations.AddField(
            model_name="video",
            name="original",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="video",
                to="backend.videofile",
            ),
        ),
    ]
