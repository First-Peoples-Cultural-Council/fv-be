# Generated by Django 4.1.7 on 2023-04-24 22:11

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0008_rename_categories_dictionaryentry_category_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dictionaryentrylink",
            name="id",
        ),
        migrations.RemoveField(
            model_name="dictionaryentryrelatedcharacter",
            name="id",
        ),
        migrations.AlterField(
            model_name="dictionaryentrylink",
            name="uuid",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="dictionaryentryrelatedcharacter",
            name="uuid",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
