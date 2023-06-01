# Generated by Django 4.2.1 on 2023-06-01 21:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("backend", "0027_merge_20230525_1714"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="groups",
            field=models.ManyToManyField(
                blank=True,
                help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                related_name="user_set",
                related_query_name="user",
                to="auth.group",
                verbose_name="groups",
            ),
        ),
    ]
