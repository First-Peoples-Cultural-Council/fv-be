# Migration file to load initial data for the following models: AppJson and PartsOfSpeech
#
# Steps:
# * set the created and last modified fields for the relevant models to be nullable
# * loads the default fixtures
# * sets the created and last_updated fields for the newly added entries
# * revert the created and last modified fields to be non-nullable
#
# This is done as a migration to avoid problems with the loaddata command using the most up-to-date models.
# The historical model at this point in the migration matches the data fixtures used.
# See both answers by @djvg and @Rockallite in the following link:
# Ref: https://stackoverflow.com/questions/25960850/

from django.apps import apps as current_apps
from django.core.management import call_command
from django.core.serializers import base, python
from django.db import migrations, models
from django.db.models import Q
from django.utils import timezone

import backend.models.part_of_speech


def load_default_fixtures(apps, schema_editor):
    old_get_model = python._get_model

    def _get_model(model_identifier):
        try:
            """add natural_key method from current model to historical model"""
            historical_model = apps.get_model(model_identifier)
            current_model = current_apps.get_model(model_identifier)
            if hasattr(current_model, "natural_key"):
                historical_model.natural_key = current_model.natural_key
            return historical_model
        except (LookupError, TypeError):
            raise base.DeserializationError(
                "Invalid model identifier: '%s'" % model_identifier
            )

    python._get_model = _get_model

    try:
        call_command("loaddata", "appjson-defaults.json", app_label="backend")
        call_command("loaddata", "default_g2p_config.json", app_label="backend")
        call_command("loaddata", "partsOfSpeech_initial.json", app_label="backend")
    finally:
        python._get_model = old_get_model


def populate_dates(apps, schema_editor):
    appjson = apps.get_model("backend", "appjson")
    for item in appjson.objects.filter(
        Q(key="default_site_menu") | Q(key="default_g2p_config")
    ):
        item.created = timezone.now()
        item.last_modified = timezone.now()
        item.save()

    partsofspeech = apps.get_model("backend", "partofspeech")
    for item in partsofspeech.objects.filter(Q(created=None) | Q(last_modified=None)):
        item.created = timezone.now()
        item.last_modified = timezone.now()
        item.save()


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0002_initial"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="partofspeech",
            managers=[
                ("objects", backend.models.part_of_speech.ParentManager()),
            ],
        ),
        migrations.AlterField(
            model_name="appjson",
            name="created",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="appjson",
            name="last_modified",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="partofspeech",
            name="created",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="partofspeech",
            name="last_modified",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True),
        ),
        migrations.RunPython(load_default_fixtures),
        migrations.RunPython(populate_dates),
    ]
