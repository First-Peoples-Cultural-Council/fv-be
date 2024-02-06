from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from backend.models.sites import Language, Site
from backend.search.tasks import language_index_tasks
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=Language)
def sync_language_in_index(sender, instance, **kwargs):
    language_index_tasks.sync_language_in_index.apply_async(
        (instance.id,), link_error=link_error_handler.s()
    )


@receiver(pre_delete, sender=Language)
def remove_language_from_index(sender, instance, **kwargs):
    language_index_tasks.remove_language_from_index.apply_async(
        (instance.id,), link_error=link_error_handler.s()
    )

    # sync any related sites
    for site in instance.sites.all():
        language_index_tasks.sync_site_in_language_index(site.id)


@receiver(pre_save, sender=Site)
def sync_site_in_language_index(sender, instance, **kwargs):
    language_index_tasks.sync_site_in_language_index.apply_async(
        (instance.id,), link_error=link_error_handler.s()
    )

    # sync related languages
    languages = []

    if instance.language:
        languages.append(instance.language)

    if instance.id:
        try:
            original_site = Site.objects.get(id=instance.id)
            if original_site.language:
                languages.append(original_site.language)

        except ObjectDoesNotExist:
            # New site, no previous language
            pass

    for language in languages:
        language_index_tasks.sync_language_in_index.apply_async(
            (language.id,), link_error=link_error_handler.s()
        )


@receiver(pre_delete, sender=Site)
def remove_site_from_language_index(sender, instance, **kwargs):
    language_index_tasks.remove_site_from_language_index.apply_async(
        (instance.id,), link_error=link_error_handler.s()
    )

    if instance.language:
        language_index_tasks.sync_language_in_index.apply_async(
            (instance.language.id,), link_error=link_error_handler.s()
        )
