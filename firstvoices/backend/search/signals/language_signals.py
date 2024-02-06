from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from backend.models.sites import Language, Site
from backend.search.tasks import language_index_tasks
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=Language)
def sync_language_in_index(sender, instance, **kwargs):
    language_index_tasks.sync_language_in_index.apply_async(
        (instance,), link_error=link_error_handler.s()
    )


@receiver(post_delete, sender=Language)
def remove_language_from_index(sender, instance, **kwargs):
    language_index_tasks.remove_language_from_index.apply_async(
        (instance,), link_error=link_error_handler.s()
    )


@receiver(pre_save, sender=Site)
def sync_site_language_in_index(sender, instance, **kwargs):
    language_index_tasks.sync_site_in_language_index.apply_async(
        (instance,), link_error=link_error_handler.s()
    )


@receiver(post_delete, sender=Site)
def remove_site_from_language_index(sender, instance, **kwargs):
    language_index_tasks.remove_site_from_language_index.apply_async(
        (instance,), link_error=link_error_handler.s()
    )
