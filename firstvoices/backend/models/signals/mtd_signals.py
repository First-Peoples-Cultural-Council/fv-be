from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from backend.models import Category, DictionaryEntry
from backend.models.constants import Visibility
from backend.tasks.build_mtd_export_format import build_index_and_calculate_scores
from firstvoices.celery import link_error_handler


def rebuild_mtd_index(site_slug):
    transaction.on_commit(
        lambda: build_index_and_calculate_scores.apply_async(
            (site_slug,),
            link_error=link_error_handler.s(),
        )
    )


@receiver(pre_save, sender=DictionaryEntry)
def store_current_visibility(sender, instance, **kwargs):
    # Adding old visibility to check later in post_save signal, if entry exists in the db
    dictionary_entry = DictionaryEntry.objects.filter(id=instance.id)
    if len(dictionary_entry):
        old_visibility = dictionary_entry[0].visibility
        instance.old_visibility = old_visibility


@receiver(post_save, sender=DictionaryEntry)
@receiver(post_delete, sender=DictionaryEntry)
def request_update_mtd_index(sender, instance, **kwargs):
    # Checking for both previous and current visibility
    # this covers the case when a word is changed from public to members/team
    if (
        hasattr(instance, "old_visibility")
        and instance.old_visibility == Visibility.PUBLIC
    ) or instance.visibility == Visibility.PUBLIC:
        rebuild_mtd_index(instance.site.slug)


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def request_update_mtd_index_category_ops(sender, instance, **kwargs):
    # Check if there are any relevant dictionary entries affected
    # relevant dictionary entries are public and have at-least one translation
    relevant_dictionary_entries_count = (
        DictionaryEntry.objects.filter(
            categories=instance, visibility=Visibility.PUBLIC
        )
        .exclude(translation_set=None)
        .count()
    )

    if relevant_dictionary_entries_count:
        rebuild_mtd_index(instance.site.slug)
