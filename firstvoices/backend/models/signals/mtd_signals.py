from django.db import transaction
from django.db.models import Count
from django.db.models.signals import m2m_changed, post_delete, post_save
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


@receiver(post_save, sender=DictionaryEntry)
@receiver(post_delete, sender=DictionaryEntry)
def request_update_mtd_index(sender, instance, **kwargs):
    if instance.visibility == Visibility.PUBLIC:
        rebuild_mtd_index(instance.site.slug)


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def request_update_mtd_index_category_ops(sender, instance, **kwargs):
    # Check if there are any relevant dictionary entries affected
    # relevant dictionary entries are public and have at-least one translation
    relevant_dictionary_entries = DictionaryEntry.objects.filter(
        categories=instance, visibility=Visibility.PUBLIC
    )
    relevant_dictionary_entries = relevant_dictionary_entries.annotate(
        translation_count=Count("translation_set")
    ).filter(translation_count__gt=0)
    if len(relevant_dictionary_entries) > 0:
        rebuild_mtd_index(instance.site.slug)


@receiver(m2m_changed, sender=DictionaryEntry.related_audio.through)
@receiver(m2m_changed, sender=DictionaryEntry.related_images.through)
def request_update_mtd_index_audio_ops(sender, instance, **kwargs):
    if instance.visibility == Visibility.PUBLIC:
        rebuild_mtd_index(instance.site.slug)
