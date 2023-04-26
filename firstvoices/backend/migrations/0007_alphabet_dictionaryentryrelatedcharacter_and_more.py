# Generated by Django 4.1.7 on 2023-04-21 21:53

import backend.models.base
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import rules.contrib.models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("backend", "0006_alter_user_password"),
    ]

    operations = [
        migrations.CreateModel(
            name="Alphabet",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("is_trashed", models.BooleanField(default=False)),
                ("created", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("last_modified", models.DateTimeField(auto_now=True, db_index=True)),
                ("input_to_canonical_map", models.JSONField(default=list)),
            ],
            options={
                "verbose_name": "alphabet mapper",
                "verbose_name_plural": "alphabet mappers",
            },
            bases=(rules.contrib.models.RulesModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="DictionaryEntryRelatedCharacter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "verbose_name": "character related dictionary entry",
                "verbose_name_plural": "character related dictionary entries",
            },
        ),
        migrations.RemoveField(
            model_name="character",
            name="related_dictionary_entries",
        ),
        migrations.AddField(
            model_name="user",
            name="date_joined",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="date joined"
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="user_permissions",
            field=models.ManyToManyField(
                blank=True,
                help_text="Specific permissions for this user.",
                related_name="user_set",
                related_query_name="user",
                to="auth.permission",
                verbose_name="user permissions",
            ),
        ),
        migrations.AlterField(
            model_name="alternatespelling",
            name="text",
            field=models.CharField(max_length=225),
        ),
        migrations.AlterField(
            model_name="category",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="backend.site",
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="title",
            field=models.CharField(max_length=75),
        ),
        migrations.AlterField(
            model_name="character",
            name="site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="backend.site",
            ),
        ),
        migrations.AlterField(
            model_name="charactervariant",
            name="site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="backend.site",
            ),
        ),
        migrations.AlterField(
            model_name="dictionaryentry",
            name="custom_order",
            field=backend.models.base.TruncatingCharField(blank=True, max_length=225),
        ),
        migrations.AlterField(
            model_name="dictionaryentry",
            name="site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="backend.site",
            ),
        ),
        migrations.AlterField(
            model_name="dictionaryentry",
            name="title",
            field=models.CharField(max_length=225),
        ),
        migrations.AlterField(
            model_name="dictionarytranslation",
            name="text",
            field=models.CharField(max_length=225),
        ),
        migrations.AlterField(
            model_name="ignoredcharacter",
            name="site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="backend.site",
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="language_family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="languages",
                to="backend.languagefamily",
            ),
        ),
        migrations.AlterField(
            model_name="membership",
            name="site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="backend.site",
            ),
        ),
        migrations.AlterField(
            model_name="partofspeech",
            name="title",
            field=models.CharField(max_length=75, unique=True),
        ),
        migrations.AlterField(
            model_name="pronunciation",
            name="text",
            field=models.CharField(max_length=225),
        ),
        migrations.AlterField(
            model_name="site",
            name="language",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sites",
                to="backend.language",
            ),
        ),
        migrations.AlterField(
            model_name="sitefeature",
            name="site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="backend.site",
            ),
        ),
        migrations.AlterField(
            model_name="sitemenu",
            name="site",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="menu",
                to="backend.site",
            ),
        ),
        migrations.DeleteModel(
            name="CharacterRelatedDictionaryEntry",
        ),
        migrations.AddField(
            model_name="dictionaryentryrelatedcharacter",
            name="character",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dictionary_entry_links",
                to="backend.character",
            ),
        ),
        migrations.AddField(
            model_name="dictionaryentryrelatedcharacter",
            name="dictionary_entry",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="character_links",
                to="backend.dictionaryentry",
            ),
        ),
        migrations.AddField(
            model_name="alphabet",
            name="created_by",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_%(app_label)s_%(class)s",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="alphabet",
            name="last_modified_by",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="modified_%(app_label)s_%(class)s",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="alphabet",
            name="site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="backend.site",
            ),
        ),
        migrations.AddField(
            model_name="dictionaryentry",
            name="related_characters",
            field=models.ManyToManyField(
                blank=True,
                related_name="dictionary_entries",
                through="backend.DictionaryEntryRelatedCharacter",
                to="backend.character",
            ),
        ),
    ]
