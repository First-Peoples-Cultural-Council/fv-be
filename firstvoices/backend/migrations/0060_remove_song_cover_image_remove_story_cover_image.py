# Generated by Django 4.2.2 on 2023-08-02 20:37

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0059_storypage_visibility"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="song",
            name="cover_image",
        ),
        migrations.RemoveField(
            model_name="story",
            name="cover_image",
        ),
    ]
