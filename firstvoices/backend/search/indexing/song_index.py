from backend.models import Song
from backend.search.documents import SongDocument
from backend.search.indexing.base import DocumentManager, IndexManager
from backend.search.utils.constants import ELASTICSEARCH_SONG_INDEX
from backend.search.utils.get_index_documents import _fields_as_list


class SongDocumentManager(DocumentManager):
    index = ELASTICSEARCH_SONG_INDEX
    document = SongDocument
    model = Song

    @classmethod
    def create_index_document(cls, instance: Song):
        """Returns a SongDocument populated for the given Song instance."""
        return SongDocument(
            document_id=str(instance.id),
            document_type=type(instance).__name__,
            site_id=str(instance.site.id),
            site_visibility=instance.site.visibility,
            exclude_from_games=instance.exclude_from_games,
            exclude_from_kids=instance.exclude_from_kids,
            visibility=instance.visibility,
            title=instance.title,
            title_translation=instance.title_translation,
            note=instance.notes,
            acknowledgement=instance.acknowledgements,
            intro_title=instance.introduction,
            intro_translation=instance.introduction_translation,
            lyrics_text=_fields_as_list(instance.lyrics, "text"),
            lyrics_translation=_fields_as_list(instance.lyrics, "translation"),
            has_audio=instance.related_audio.exists(),
            has_video=instance.related_videos.exists(),
            has_image=instance.related_images.exists(),
            created=instance.created,
            last_modified=instance.last_modified,
            has_translation=bool(instance.title_translation),
        )


class SongIndexManager(IndexManager):
    index = ELASTICSEARCH_SONG_INDEX
    document_managers = [SongDocumentManager]
