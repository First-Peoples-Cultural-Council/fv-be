# Generated by Django 4.2.4 on 2023-08-23 00:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0066_alter_sitepage_widgets"),
    ]

    operations = [
        migrations.AlterField(
            model_name="character",
            name="approximate_form",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
