# Generated by Django 4.2.1 on 2023-05-25 22:38

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0025_customorderrecalculationpreviewresult_task_id"),
    ]

    operations = [
        migrations.RenameField(
            model_name="customorderrecalculationpreviewresult",
            old_name="date",
            new_name="latest_recalculation_date",
        ),
        migrations.RenameField(
            model_name="customorderrecalculationpreviewresult",
            old_name="result",
            new_name="latest_recalculation_result",
        ),
    ]
