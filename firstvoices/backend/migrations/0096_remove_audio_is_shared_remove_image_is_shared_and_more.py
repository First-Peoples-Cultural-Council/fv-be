# Generated by Django 4.2.7 on 2024-01-29 19:33

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0095_alter_sitefeature_key"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="audio",
            name="is_shared",
        ),
        migrations.RemoveField(
            model_name="image",
            name="is_shared",
        ),
        migrations.RemoveField(
            model_name="video",
            name="is_shared",
        ),
    ]
