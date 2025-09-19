from backend.models import DictionaryEntry
from backend.search.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    UNKNOWN_CHARACTER_FLAG,
)
from backend.search.documents import DictionaryEntryDocument
from backend.search.indexing.base import DocumentManager, IndexManager
from backend.utils.as_list import fields_as_list


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
            translation=instance.translations,
            acknowledgement=instance.acknowledgements,
            alternate_spelling=instance.alternate_spellings,
            note=instance.notes,
            categories=fields_as_list(instance.categories, "id"),
            import_job_id=instance.import_job.id if instance.import_job else None,
            external_system=(
                instance.external_system.id if instance.external_system else None
            ),
            exclude_from_kids=instance.exclude_from_kids,
            exclude_from_games=instance.exclude_from_games,
            custom_order=instance.custom_order,
            visibility=instance.visibility,
            has_audio=instance.related_audio.exists(),
            has_document=instance.related_documents.exists(),
            has_image=instance.related_images.exists(),
            has_video=instance.related_videos.exists()
            or bool(instance.related_video_links),
            created=instance.created,
            last_modified=instance.last_modified,
            has_translation=(len(instance.translations) > 0),
            has_unrecognized_chars=UNKNOWN_CHARACTER_FLAG in instance.custom_order,
            has_categories=instance.categories.exists(),
            has_related_entries=instance.related_dictionary_entries.exists(),
        )


class DictionaryIndexManager(IndexManager):
    index = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
    document_managers = [DictionaryEntryDocumentManager]
