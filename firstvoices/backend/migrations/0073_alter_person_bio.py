# Generated by Django 4.2.4 on 2023-09-18 23:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0072_remove_category_category_site_title_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="bio",
            field=models.CharField(blank=True, max_length=1000),
        ),
    ]
