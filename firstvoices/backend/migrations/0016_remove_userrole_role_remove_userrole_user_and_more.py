# Generated by Django 4.1.7 on 2023-05-04 18:13

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0015_alter_dictionaryentrylink_options_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userrole",
            name="role",
        ),
        migrations.RemoveField(
            model_name="userrole",
            name="user",
        ),
        migrations.DeleteModel(
            name="Role",
        ),
        migrations.DeleteModel(
            name="UserRole",
        ),
    ]
