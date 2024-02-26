from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from backend.models.sites import Language, LanguageFamily, Site
from backend.search.indexing.language_index import (
    LanguageDocumentManager,
    SiteDocumentManager,
)
from backend.search.tasks.index_manager_tasks import (
    request_remove_from_index,
    request_sync_in_index,
)


@receiver(post_save, sender=LanguageFamily)
def sync_language_family_in_index(sender, instance, **kwargs):
    for language in instance.languages.all():
        request_sync_in_index(LanguageDocumentManager, language)


# note: no signal needed for deleting a LanguageFamily, because the model can only be deleted once it has
# no Languages associated


@receiver(post_save, sender=Language)
def sync_language_in_index(sender, instance, **kwargs):
    request_sync_in_index(LanguageDocumentManager, instance)


@receiver(pre_delete, sender=Language)
def remove_language_from_index(sender, instance, **kwargs):
    request_remove_from_index(LanguageDocumentManager, instance)

    # sync any related sites
    for site in instance.sites.all():
        request_sync_in_index(SiteDocumentManager, site)


@receiver(pre_save, sender=Site)
def sync_site_in_language_index(sender, instance, **kwargs):
    request_sync_in_index(SiteDocumentManager, instance)

    # sync related languages
    languages = set()

    if instance.language:
        languages.add(instance.language)

    if instance.id:
        try:
            original_site = Site.objects.get(id=instance.id)
            if original_site.language:
                languages.add(original_site.language)

        except ObjectDoesNotExist:
            # New site, no previous language
            pass

    for language in languages:
        request_sync_in_index(LanguageDocumentManager, language)


@receiver(pre_delete, sender=Site)
def remove_site_from_language_index(sender, instance, **kwargs):
    request_remove_from_index(SiteDocumentManager, instance)

    if instance.language:
        request_sync_in_index(LanguageDocumentManager, instance.language)
