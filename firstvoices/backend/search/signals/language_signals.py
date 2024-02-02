from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from backend.models.sites import Language, Site
from backend.search.indexing import LanguageIndexManager
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=Language)
def sync_language_in_index(sender, instance, **kwargs):
    LanguageIndexManager.sync_in_index.apply_async(
        (instance,), link_error=link_error_handler.s()
    )


@receiver(pre_save, sender=Site)
def sync_site_language_in_index(sender, instance, **kwargs):
    languages = []

    if instance.language:
        languages.push(instance.language)

    if instance.id:
        try:
            original_site = Site.objects.get(id=instance.id)
            if original_site.language:
                languages.push(original_site.language)

        except ObjectDoesNotExist:
            # New site, no previous language to index
            pass

    for language in languages:
        LanguageIndexManager.sync_in_index.apply_async(
            (language,), link_error=link_error_handler.s()
        )


@receiver(post_delete, sender=Language)
def remove_language_from_index(sender, instance, **kwargs):
    LanguageIndexManager.remove_from_index(instance)
