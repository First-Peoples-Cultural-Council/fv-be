# Generated by Django 4.1.7 on 2023-04-28 21:06

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0013_acknowledgement_note_translation_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="category",
            unique_together={("site", "title")},
        ),
    ]
