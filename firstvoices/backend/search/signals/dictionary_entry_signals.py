from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from backend.models.dictionary import (
    DictionaryEntry,
    DictionaryEntryCategory,
    DictionaryEntryLink,
)
from backend.search.indexing.dictionary_index import DictionaryEntryDocumentManager
from backend.search.signals.site_signals import indexing_signals_paused
from backend.search.tasks.index_manager_tasks import (
    request_remove_from_index,
    request_sync_in_index,
    request_update_in_index,
)


@receiver(post_save, sender=DictionaryEntry)
def sync_dictionary_entry_in_index(sender, instance, **kwargs):
    if not indexing_signals_paused(instance.site):
        request_sync_in_index(DictionaryEntryDocumentManager, instance)


@receiver(post_delete, sender=DictionaryEntry)
def remove_dictionary_entry_from_index(sender, instance, **kwargs):
    if not indexing_signals_paused(instance.site):
        request_remove_from_index(DictionaryEntryDocumentManager, instance)


@receiver(
    post_save, sender=DictionaryEntryCategory
)  # Category update via creating m2m model (admin site does this)
@receiver(
    post_delete, sender=DictionaryEntryCategory
)  # Category update via creating m2m model (admin site does this)
def sync_dictionary_entry_category_in_index(sender, instance, **kwargs):
    if not indexing_signals_paused(instance.site):
        request_update_in_index(
            DictionaryEntryDocumentManager, instance.dictionary_entry
        )


@receiver(
    m2m_changed, sender=DictionaryEntryCategory
)  # Category update via m2m manager (APIs do this)
@receiver(
    m2m_changed, sender=DictionaryEntryLink
)  # Related entry update via m2m manager (APIs do this)
def request_update_dictionary_entry_m2m_index(sender, instance, **kwargs):
    if not indexing_signals_paused(instance.site):
        request_update_in_index(DictionaryEntryDocumentManager, instance)


@receiver(
    post_save, sender=DictionaryEntryLink
)  # Related entry update via creating m2m model (admin site does this)
@receiver(
    post_delete, sender=DictionaryEntryLink
)  # Related entry update via creating m2m model (admin site does this)
def sync_related_dictionary_entry_in_index(sender, instance, **kwargs):
    if not indexing_signals_paused(instance.site):
        request_update_in_index(
            DictionaryEntryDocumentManager, instance.from_dictionary_entry
        )
        request_update_in_index(
            DictionaryEntryDocumentManager, instance.to_dictionary_entry
        )
