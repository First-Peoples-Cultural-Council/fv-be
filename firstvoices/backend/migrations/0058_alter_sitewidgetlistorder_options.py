# Generated by Django 4.2.3 on 2023-07-28 23:43

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0057_storypage_alter_song_unique_together_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sitewidgetlistorder",
            options={
                "ordering": ("order",),
                "verbose_name": "site widget list order",
                "verbose_name_plural": "site widget list orders",
            },
        ),
    ]
