# Generated by Django 4.2.3 on 2023-07-20 18:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0051_sitepage_remove_site_only_one_banner_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dictionaryentry",
            name="type",
            field=models.CharField(
                choices=[("word", "Word"), ("phrase", "Phrase")],
                default="word",
                max_length=6,
            ),
        ),
    ]
