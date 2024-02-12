from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from backend.models.dictionary import (
    Acknowledgement,
    DictionaryEntry,
    DictionaryEntryCategory,
    Note,
    Translation,
)
from backend.search.indexing.dictionary_index import DictionaryEntryDocumentManager
from backend.search.tasks.index_manager_tasks import (
    request_remove_from_index,
    request_sync_in_index,
)


@receiver(post_save, sender=DictionaryEntry)
def sync_dictionary_entry_in_index(sender, instance, **kwargs):
    request_sync_in_index(DictionaryEntryDocumentManager, instance)


@receiver(post_delete, sender=DictionaryEntry)
def remove_dictionary_entry_from_index(sender, instance, **kwargs):
    request_remove_from_index(DictionaryEntryDocumentManager, instance)


@receiver(post_delete, sender=Translation)
@receiver(post_save, sender=Translation)
@receiver(post_delete, sender=Note)
@receiver(post_save, sender=Note)
@receiver(post_delete, sender=Acknowledgement)
@receiver(post_save, sender=Acknowledgement)
@receiver(
    post_save, sender=DictionaryEntryCategory
)  # Category update when called through the admin site
@receiver(
    post_delete, sender=DictionaryEntryCategory
)  # Category update when called through the admin site
def sync_related_dictionary_entry_in_index(sender, instance, **kwargs):
    request_sync_in_index(DictionaryEntryDocumentManager, instance.dictionary_entry)


@receiver(
    m2m_changed, sender=DictionaryEntryCategory
)  # Category update when called through the APIs
def sync_dictionary_entry_by_category_in_index(sender, instance, **kwargs):
    request_sync_in_index(DictionaryEntryDocumentManager, instance)
