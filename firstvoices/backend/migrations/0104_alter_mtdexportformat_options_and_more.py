# Generated by Django 4.2.7 on 2024-04-26 17:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0103_importjobreport_alter_category_description_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="mtdexportformat",
            options={
                "get_latest_by": "created",
                "verbose_name": "Mother Tongues dictionary export format result",
                "verbose_name_plural": "Mother Tongues dictionary export format results",
            },
        ),
        migrations.RemoveField(
            model_name="mtdexportformat",
            name="latest_export_date",
        ),
    ]
