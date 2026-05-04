# This migration combined with 0131 replaces the migrations 0003 and 0004 to prepare for future version upgrades.
# The older migrations use the python._get_model API which is now removed.

from django.db import migrations, models
from backend.models import part_of_speech

class Migration(migrations.Migration):

    replaces = [
        ("backend", "0003_load_initial_data_fixtures"),
        ("backend", "0004_load_languagefamily_language_data"),
    ]

    dependencies = [
        ("backend", "0002_initial"),
    ]

    operations = [
        # from 0003
        migrations.AlterModelManagers(
            name="partofspeech",
            managers=[
                ("objects", part_of_speech.ParentManager()),
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

        # from 0004
        migrations.AlterField(
            model_name="languagefamily",
            name="created",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="languagefamily",
            name="last_modified",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="language",
            name="created",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="language",
            name="last_modified",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True),
        ),
    ]
