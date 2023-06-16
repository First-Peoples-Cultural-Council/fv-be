# Generated by Django 4.2.2 on 2023-06-16 10:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0039_translatedtext_song"),
    ]

    operations = [
        migrations.AlterField(
            model_name="song",
            name="introduction",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="song",
            name="introduction_translations",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="backend.translatedtext",
            ),
        ),
        migrations.AlterField(
            model_name="song",
            name="lyrics",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="song",
            name="lyrics_translations",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="backend.translatedtext",
            ),
        ),
        migrations.AlterField(
            model_name="song",
            name="title_translations",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="backend.translatedtext",
            ),
        ),
    ]
