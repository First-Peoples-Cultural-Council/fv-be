from django.db.models import signals

from backend.models import Acknowledgement, DictionaryEntry, Note, Site, Translation
from backend.models.dictionary import DictionaryEntryCategory
from backend.search.signals.dictionary_entry_signals import (
    remove_dictionary_entry_from_index,
    request_update_acknowledgement_index,
    request_update_categories_index,
    request_update_categories_m2m_index,
    request_update_notes_index,
    sync_dictionary_entry_in_index,
    sync_related_dictionary_entry_in_index,
)
from backend.search.signals.site_signals import (
    change_site_visibility,
    request_delete_related_docs,
)


def disconnect_signals():
    # Disconnect signals temporarily
    # Verify the list with signals present in all index documents present in
    # backend.search folder if this list goes out of sync

    # backend.search.signals.dictionary_entry_signals
    signals.post_save.disconnect(sync_dictionary_entry_in_index, sender=DictionaryEntry)
    signals.post_delete.disconnect(
        remove_dictionary_entry_from_index, sender=DictionaryEntry
    )
    signals.post_save.disconnect(
        sync_related_dictionary_entry_in_index, sender=Translation
    )
    signals.post_delete.disconnect(
        sync_related_dictionary_entry_in_index, sender=Translation
    )
    signals.post_save.disconnect(request_update_notes_index, sender=Note)
    signals.post_delete.disconnect(request_update_notes_index, sender=Note)
    signals.post_save.disconnect(
        request_update_acknowledgement_index, sender=Acknowledgement
    )
    signals.post_delete.disconnect(
        request_update_acknowledgement_index, sender=Acknowledgement
    )
    signals.post_save.disconnect(
        request_update_categories_index, sender=DictionaryEntryCategory
    )
    signals.post_delete.disconnect(
        request_update_categories_index, sender=DictionaryEntryCategory
    )
    signals.m2m_changed.disconnect(
        request_update_categories_m2m_index, sender=DictionaryEntryCategory
    )

    # backend.search.signals.song_signals
    # backend.search.signals.story_signals

    # backend.search.signals.media_signals

    # backend.search.utils.site_signals
    signals.pre_save.disconnect(change_site_visibility, sender=Site)
    signals.post_delete.disconnect(request_delete_related_docs, sender=Site)


def reconnect_signals():
    # Reconnect signals back to models
    # Verify the list with signals present in all index documents present in
    # backend.search folder if this list goes out of sync

    # backend.search.signals.dictionary_entry_signals
    signals.post_save.connect(sync_dictionary_entry_in_index, sender=DictionaryEntry)
    signals.post_delete.connect(
        remove_dictionary_entry_from_index, sender=DictionaryEntry
    )
    signals.post_save.connect(
        sync_related_dictionary_entry_in_index, sender=Translation
    )
    signals.post_delete.connect(
        sync_related_dictionary_entry_in_index, sender=Translation
    )
    signals.post_save.connect(request_update_notes_index, sender=Note)
    signals.post_delete.connect(request_update_notes_index, sender=Note)
    signals.post_save.connect(
        request_update_acknowledgement_index, sender=Acknowledgement
    )
    signals.post_delete.connect(
        request_update_acknowledgement_index, sender=Acknowledgement
    )
    signals.post_save.connect(
        request_update_categories_index, sender=DictionaryEntryCategory
    )
    signals.post_delete.connect(
        request_update_categories_index, sender=DictionaryEntryCategory
    )
    signals.m2m_changed.connect(
        request_update_categories_m2m_index, sender=DictionaryEntryCategory
    )

    # backend.search.signals.song_signals

    # backend.search.signals.story_signals

    # backend.search.signals.media_signals

    # backend.search.utils.site_signals
    signals.pre_save.connect(change_site_visibility, sender=Site)
    signals.post_delete.connect(request_delete_related_docs, sender=Site)
