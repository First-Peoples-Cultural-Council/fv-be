# Generated by Django 4.2.4 on 2023-08-17 21:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0065_alter_widget_format"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitepage",
            name="widgets",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sitepage_set",
                to="backend.sitewidgetlist",
            ),
        ),
    ]
