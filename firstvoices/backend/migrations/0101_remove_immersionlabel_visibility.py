# Generated by Django 4.2.7 on 2024-03-28 18:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0100_alter_language_community_keywords"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="immersionlabel",
            name="visibility",
        ),
    ]
