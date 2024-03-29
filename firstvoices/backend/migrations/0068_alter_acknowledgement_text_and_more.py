# Generated by Django 4.2.4 on 2023-08-29 23:55

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0067_alter_character_approximate_form"),
    ]

    operations = [
        migrations.AlterField(
            model_name="acknowledgement",
            name="text",
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name="dictionaryentry",
            name="batch_id",
            field=models.CharField(blank=True),
        ),
        migrations.AlterField(
            model_name="lyric",
            name="text",
            field=models.TextField(max_length=1500),
        ),
        migrations.AlterField(
            model_name="lyric",
            name="translation",
            field=models.TextField(blank=True, max_length=1500),
        ),
        migrations.AlterField(
            model_name="note",
            name="text",
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name="song",
            name="acknowledgements",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=500),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="song",
            name="introduction",
            field=models.TextField(blank=True, max_length=1500),
        ),
        migrations.AlterField(
            model_name="song",
            name="introduction_translation",
            field=models.TextField(blank=True, max_length=1500),
        ),
        migrations.AlterField(
            model_name="song",
            name="notes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=500),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="song",
            name="title",
            field=models.CharField(max_length=225),
        ),
        migrations.AlterField(
            model_name="song",
            name="title_translation",
            field=models.CharField(blank=True, max_length=225),
        ),
        migrations.AlterField(
            model_name="story",
            name="acknowledgements",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=500),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="story",
            name="author",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="story",
            name="introduction",
            field=models.TextField(blank=True, max_length=1500),
        ),
        migrations.AlterField(
            model_name="story",
            name="introduction_translation",
            field=models.TextField(blank=True, max_length=1500),
        ),
        migrations.AlterField(
            model_name="story",
            name="notes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=500),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="story",
            name="title",
            field=models.CharField(max_length=225),
        ),
        migrations.AlterField(
            model_name="story",
            name="title_translation",
            field=models.CharField(blank=True, max_length=225),
        ),
        migrations.AlterField(
            model_name="storypage",
            name="notes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=500),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="storypage",
            name="text",
            field=models.TextField(max_length=1500),
        ),
        migrations.AlterField(
            model_name="storypage",
            name="translation",
            field=models.TextField(blank=True, max_length=1500),
        ),
    ]
