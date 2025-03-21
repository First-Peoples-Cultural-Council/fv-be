# Generated by Django 5.1.1 on 2024-10-30 22:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0116_dictionaryentry_import_job"),
    ]

    operations = [
        migrations.AddField(
            model_name="file",
            name="import_job",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="backend.importjob",
            ),
        ),
        migrations.AddField(
            model_name="imagefile",
            name="import_job",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="backend.importjob",
            ),
        ),
        migrations.AddField(
            model_name="videofile",
            name="import_job",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="backend.importjob",
            ),
        ),
    ]
