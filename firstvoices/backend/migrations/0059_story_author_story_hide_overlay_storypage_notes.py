# Generated by Django 4.2.2 on 2023-07-27 17:42

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0058_storypage_site"),
    ]

    operations = [
        migrations.AddField(
            model_name="story",
            name="author",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="story",
            name="hide_overlay",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="storypage",
            name="notes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(max_length=1000),
                blank=True,
                default=list,
                size=None,
            ),
        ),
    ]
