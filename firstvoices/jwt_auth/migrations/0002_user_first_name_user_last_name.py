# Generated by Django 4.2.6 on 2023-11-09 18:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jwt_auth", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="first_name",
            field=models.CharField(
                blank=True, max_length=150, verbose_name="first name"
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="last_name",
            field=models.CharField(
                blank=True, max_length=150, verbose_name="last name"
            ),
        ),
    ]