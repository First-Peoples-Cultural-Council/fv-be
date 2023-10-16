from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from backend.models.dictionary import (
    Acknowledgement,
    DictionaryEntry,
    DictionaryEntryCategory,
    Note,
    Translation,
)
from backend.search.tasks.dictionary_entry_tasks import (
    delete_from_index,
    update_acknowledgements,
    update_categories,
    update_categories_m2m,
    update_dictionary_entry_index,
    update_notes,
    update_translation,
)
from backend.search.utils.constants import ES_RETRY_POLICY
from firstvoices.celery import check_celery_status, link_error_handler


# Signal to update the entry in index
@receiver(post_save, sender=DictionaryEntry)
def request_update_dictionary_entry_index(sender, instance, **kwargs):
    check_celery_status("update_dictionary_entry_index", instance.id)
    if DictionaryEntry.objects.filter(id=instance.id).exists():
        transaction.on_commit(
            lambda: update_dictionary_entry_index.apply_async(
                (instance.id,),
                link_error=link_error_handler.s(),
                retry=True,
                retry_policy=ES_RETRY_POLICY,
            )
        )


# Delete entry from index
@receiver(post_delete, sender=DictionaryEntry)
def request_delete_dictionary_entry_index(sender, instance, **kwargs):
    check_celery_status("delete_from_index", instance.id)
    delete_from_index.apply_async((instance.id,), link_error=link_error_handler.s())


# Translation update
@receiver(post_delete, sender=Translation)
@receiver(post_save, sender=Translation)
def request_update_translation_index(sender, instance, **kwargs):
    check_celery_status("update_translation", instance.id)
    if DictionaryEntry.objects.filter(id=instance.dictionary_entry.id).exists():
        transaction.on_commit(
            lambda: update_translation.apply_async(
                (
                    instance.id,
                    instance.dictionary_entry.id,
                ),
                link_error=link_error_handler.s(),
                retry=True,
                retry_policy=ES_RETRY_POLICY,
            )
        )


# Note update
@receiver(post_delete, sender=Note)
@receiver(post_save, sender=Note)
def request_update_notes_index(sender, instance, **kwargs):
    check_celery_status("update_notes", instance.id)
    if DictionaryEntry.objects.filter(id=instance.dictionary_entry.id).exists():
        transaction.on_commit(
            lambda: update_notes.apply_async(
                (
                    instance.id,
                    instance.dictionary_entry.id,
                ),
                link_error=link_error_handler.s(),
                retry=True,
                retry_policy=ES_RETRY_POLICY,
            )
        )


# Acknowledgement update
@receiver(post_delete, sender=Acknowledgement)
@receiver(post_save, sender=Acknowledgement)
def request_update_acknowledgement_index(sender, instance, **kwargs):
    check_celery_status("update_acknowledgements", instance.id)
    if DictionaryEntry.objects.filter(id=instance.dictionary_entry.id).exists():
        transaction.on_commit(
            lambda: update_acknowledgements.apply_async(
                (
                    instance.id,
                    instance.dictionary_entry.id,
                ),
                link_error=link_error_handler.s(),
                retry=True,
                retry_policy=ES_RETRY_POLICY,
            )
        )


# Category update when called through the admin site
@receiver(post_save, sender=DictionaryEntryCategory)
@receiver(post_delete, sender=DictionaryEntryCategory)
def request_update_categories_index(sender, instance, **kwargs):
    check_celery_status("update_categories", instance.id)
    transaction.on_commit(
        lambda: update_categories.apply_async(
            (instance.id,),
            link_error=link_error_handler.s(),
            retry=True,
            retry_policy=ES_RETRY_POLICY,
        )
    )


# Category update when called through the APIs
@receiver(m2m_changed, sender=DictionaryEntryCategory)
def request_update_categories_m2m_index(sender, instance, **kwargs):
    check_celery_status("update_categories_m2m", instance.id)
    update_categories_m2m.apply_async(
        (instance.id,),
        link_error=link_error_handler.s(),
        retry=True,
        retry_policy=ES_RETRY_POLICY,
    )
