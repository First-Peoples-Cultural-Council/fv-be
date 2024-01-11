# Generated by Django 4.2.7 on 2024-01-08 19:17

import backend.models.validators
from django.db import migrations
import django_better_admin_arrayfield.models.fields
import embed_video.fields


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0091_delete_embeddedvideo"),
    ]

    operations = [
        migrations.AddField(
            model_name="character",
            name="related_video_links",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=embed_video.fields.EmbedVideoField(),
                blank=True,
                default=list,
                size=None,
                validators=[backend.models.validators.validate_no_duplicate_urls],
            ),
        ),
        migrations.AddField(
            model_name="dictionaryentry",
            name="related_video_links",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=embed_video.fields.EmbedVideoField(),
                blank=True,
                default=list,
                size=None,
                validators=[backend.models.validators.validate_no_duplicate_urls],
            ),
        ),
        migrations.AddField(
            model_name="song",
            name="related_video_links",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=embed_video.fields.EmbedVideoField(),
                blank=True,
                default=list,
                size=None,
                validators=[backend.models.validators.validate_no_duplicate_urls],
            ),
        ),
        migrations.AddField(
            model_name="story",
            name="related_video_links",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=embed_video.fields.EmbedVideoField(),
                blank=True,
                default=list,
                size=None,
                validators=[backend.models.validators.validate_no_duplicate_urls],
            ),
        ),
        migrations.AddField(
            model_name="storypage",
            name="related_video_links",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=embed_video.fields.EmbedVideoField(),
                blank=True,
                default=list,
                size=None,
                validators=[backend.models.validators.validate_no_duplicate_urls],
            ),
        ),
    ]
