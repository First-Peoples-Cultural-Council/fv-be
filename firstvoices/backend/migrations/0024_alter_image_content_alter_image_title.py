# Generated by Django 4.2.1 on 2023-05-24 16:15

import backend.models.media
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0023_alter_image_content"),
    ]

    operations = [
        migrations.AlterField(
            model_name="image",
            name="content",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=backend.models.media.user_directory_path,
            ),
        ),
        migrations.AlterField(
            model_name="image",
            name="title",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
