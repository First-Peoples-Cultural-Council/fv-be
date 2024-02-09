from backend.models import Song
from backend.search.documents import SongDocument
from backend.search.indexing.base import IndexManager, SiteContentDocumentManager
from backend.search.utils.constants import ELASTICSEARCH_SONG_INDEX
from backend.search.utils.get_index_documents import fields_as_list


class SongDocumentManager(SiteContentDocumentManager):
    index = ELASTICSEARCH_SONG_INDEX
    document = SongDocument
    model = Song

    @classmethod
    def create_index_document(cls, instance: Song):
        """Returns a SongDocument populated for the given Song instance."""
        return cls.document(
            document_id=str(instance.id),
            document_type=type(instance).__name__,
            site_id=str(instance.site.id),
            site_visibility=instance.site.visibility,
            visibility=instance.visibility,
            title=instance.title,
            title_translation=instance.title_translation,
            has_translation=bool(instance.title_translation),
            intro_title=instance.introduction,
            intro_translation=instance.introduction_translation,
            lyrics_text=fields_as_list(instance.lyrics, "text"),
            lyrics_translation=fields_as_list(instance.lyrics, "translation"),
            note=instance.notes,
            acknowledgement=instance.acknowledgements,
            has_audio=instance.related_audio.exists(),
            has_video=instance.related_videos.exists(),
            has_image=instance.related_images.exists(),
            exclude_from_games=instance.exclude_from_games,
            exclude_from_kids=instance.exclude_from_kids,
            created=instance.created,
            last_modified=instance.last_modified,
        )


class SongIndexManager(IndexManager):
    index = ELASTICSEARCH_SONG_INDEX
    document_managers = [SongDocumentManager]
