# Generated by Django 4.2.2 on 2023-07-31 21:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0058_alter_sitewidgetlistorder_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="storypage",
            name="visibility",
            field=models.IntegerField(
                choices=[(0, "Team"), (10, "Members"), (20, "Public")], default=0
            ),
        ),
    ]
