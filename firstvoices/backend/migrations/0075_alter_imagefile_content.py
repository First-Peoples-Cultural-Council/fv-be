# Generated by Django 4.2.5 on 2023-09-22 02:25

import backend.models.media
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0074_alter_dictionaryentry_visibility_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="imagefile",
            name="content",
            field=models.ImageField(
                max_length=500, upload_to=backend.models.media.media_directory_path
            ),
        ),
    ]
