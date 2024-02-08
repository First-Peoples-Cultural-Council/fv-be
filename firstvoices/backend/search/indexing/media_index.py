from backend.models.constants import Visibility
from backend.models.media import Audio, Image, Video
from backend.search.documents import MediaDocument
from backend.search.indexing.base import DocumentManager, IndexManager
from backend.search.utils.constants import ELASTICSEARCH_MEDIA_INDEX


class MediaDocumentManager(DocumentManager):
    index = ELASTICSEARCH_MEDIA_INDEX
    document = MediaDocument
    model = None

    @classmethod
    def create_index_document(cls, instance):
        """Returns a MediaDocument populated for the given media instance."""
        return cls.document(
            document_id=str(instance.id),
            document_type=type(instance).__name__,
            site_id=str(instance.site.id),
            site_visibility=instance.site.visibility,
            visibility=Visibility.PUBLIC,
            title=instance.title,
            filename=instance.original.content.name,
            description=instance.description,
            type=type(instance).__name__.lower(),
            exclude_from_games=instance.exclude_from_games,
            exclude_from_kids=instance.exclude_from_kids,
            created=instance.created,
            last_modified=instance.last_modified,
        )


class AudioDocumentManager(MediaDocumentManager):
    model = Audio


class ImageDocumentManager(MediaDocumentManager):
    model = Image


class VideoDocumentManager(MediaDocumentManager):
    model = Video


class MediaIndexManager(IndexManager):
    index = ELASTICSEARCH_MEDIA_INDEX
    document_managers = [
        VideoDocumentManager,
        ImageDocumentManager,
        AudioDocumentManager,
    ]
