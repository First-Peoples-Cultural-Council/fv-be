from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from backend.models.sites import Site
from backend.search.tasks.site_tasks import (
    delete_related_docs,
    update_document_visibility,
)
from firstvoices.celery import link_error_handler


# If a site's visibility is changed, update all docs from index related to site
@receiver(pre_save, sender=Site)
def request_update_document_visibility(sender, instance, **kwargs):
    if instance.id is None:
        # New site, don't do anything
        return

    try:
        original_site = Site.objects.get(id=instance.id)
    except ObjectDoesNotExist:
        # New site or deleted, don't do anything
        return

    if original_site.visibility != instance.visibility:
        update_document_visibility.apply_async(
            (instance.id, instance.visibility), link_error=link_error_handler.s()
        )


# If a site is deleted, delete all docs from index related to site
@receiver(post_delete, sender=Site)
def request_delete_related_docs(sender, instance, **kwargs):
    if Site.objects.filter(id=instance.id).exists():
        delete_related_docs.apply_async(
            (instance.id,), link_error=link_error_handler.s()
        )
