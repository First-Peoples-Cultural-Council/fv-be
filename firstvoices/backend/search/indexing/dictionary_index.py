from backend.models import DictionaryEntry
from backend.search.documents import DictionaryEntryDocument
from backend.search.indexing.base import DocumentManager, IndexManager
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    UNKNOWN_CHARACTER_FLAG,
)
from backend.search.utils.get_index_documents import fields_as_list


class DictionaryEntryDocumentManager(DocumentManager):
    index = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
    document = DictionaryEntryDocument
    model = DictionaryEntry

    @classmethod
    def create_index_document(cls, instance: DictionaryEntry):
        """Returns a DictionaryEntryDocument populated for the given DictionaryEntry instance."""
        return cls.document(
            document_id=str(instance.id),
            document_type=type(instance).__name__,
            site_id=str(instance.site.id),
            site_visibility=instance.site.visibility,
            title=instance.title,
            type=instance.type,
            translation=fields_as_list(instance.translation_set, "text"),
            acknowledgement=fields_as_list(instance.acknowledgement_set, "text"),
            note=fields_as_list(instance.note_set, "text"),
            categories=fields_as_list(instance.categories, "id"),
            exclude_from_kids=instance.exclude_from_kids,
            exclude_from_games=instance.exclude_from_games,
            custom_order=instance.custom_order,
            visibility=instance.visibility,
            has_audio=instance.related_audio.exists(),
            has_video=instance.related_videos.exists()
            or instance.related_video_links.exists(),
            has_image=instance.related_images.exists(),
            created=instance.created,
            last_modified=instance.last_modified,
            has_translation=instance.translation_set.exists(),
            has_unrecognized_chars=UNKNOWN_CHARACTER_FLAG in instance.custom_order,
        )


class DictionaryIndexManager(IndexManager):
    index = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
    document_managers = [DictionaryEntryDocumentManager]
