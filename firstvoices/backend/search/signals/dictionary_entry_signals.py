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
from firstvoices.celery import link_error_handler


# Signal to update the entry in index
@receiver(post_save, sender=DictionaryEntry)
def request_update_dictionary_entry_index(sender, instance, **kwargs):
    if DictionaryEntry.objects.filter(id=instance.id).exists():
        update_dictionary_entry_index.apply_async(
            (instance.id,),
            link_error=link_error_handler.s(),
            retry=True,
            retry_policy={
                "max_retries": 3,
                "interval_start": 3,
                "interval_step": 1,
            },
        )


# Delete entry from index
@receiver(post_delete, sender=DictionaryEntry)
def request_delete_dictionary_entry_index(sender, instance, **kwargs):
    delete_from_index.apply_async((instance.id,), link_error=link_error_handler.s())


# Translation update
@receiver(post_delete, sender=Translation)
@receiver(post_save, sender=Translation)
def request_update_translation_index(sender, instance, **kwargs):
    update_translation.apply_async(
        (
            instance.id,
            instance.dictionary_entry.id,
        ),
        link_error=link_error_handler.s(),
        retry=True,
        retry_policy={
            "max_retries": 3,
            "interval_start": 3,
            "interval_step": 1,
        },
    )


# Note update
@receiver(post_delete, sender=Note)
@receiver(post_save, sender=Note)
def request_update_notes_index(sender, instance, **kwargs):
    update_notes.apply_async(
        (
            instance.id,
            instance.dictionary_entry.id,
        ),
        link_error=link_error_handler.s(),
        retry=True,
        retry_policy={
            "max_retries": 3,
            "interval_start": 3,
            "interval_step": 1,
        },
    )


# Acknowledgement update
@receiver(post_delete, sender=Acknowledgement)
@receiver(post_save, sender=Acknowledgement)
def request_update_acknowledgement_index(sender, instance, **kwargs):
    update_acknowledgements.apply_async(
        (
            instance.id,
            instance.dictionary_entry.id,
        ),
        link_error=link_error_handler.s(),
        retry=True,
        retry_policy={
            "max_retries": 3,
            "interval_start": 3,
            "interval_step": 1,
        },
    )


# Category update when called through the admin site
@receiver(post_save, sender=DictionaryEntryCategory)
@receiver(post_delete, sender=DictionaryEntryCategory)
def request_update_categories_index(sender, instance, **kwargs):
    update_categories.apply_async(
        (instance.id,),
        link_error=link_error_handler.s(),
        retry=True,
        retry_policy={
            "max_retries": 3,
            "interval_start": 3,
            "interval_step": 1,
        },
    )


# Category update when called through the APIs
@receiver(m2m_changed, sender=DictionaryEntryCategory)
def request_update_categories_m2m_index(sender, instance, **kwargs):
    update_categories_m2m.apply_async(
        (instance.id,),
        link_error=link_error_handler.s(),
        retry=True,
        retry_policy={
            "max_retries": 3,
            "interval_start": 3,
            "interval_step": 1,
        },
    )
