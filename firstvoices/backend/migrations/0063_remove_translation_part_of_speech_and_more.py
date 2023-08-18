# Generated by Django 4.2.4 on 2023-08-16 18:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0062_alter_file_content_alter_imagefile_content_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="translation",
            name="part_of_speech",
        ),
        migrations.AddField(
            model_name="dictionaryentry",
            name="part_of_speech",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="dictionary_entries",
                to="backend.partofspeech",
            ),
        ),
    ]