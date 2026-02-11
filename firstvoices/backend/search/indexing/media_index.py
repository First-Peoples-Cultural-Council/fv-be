from backend.models.constants import Visibility
from backend.models.media import Audio, Document, Image, Video
from backend.search.constants import ELASTICSEARCH_MEDIA_INDEX
from backend.search.documents import MediaDocument
from backend.search.indexing.base import DocumentManager, IndexManager


class MediaDocumentManager(DocumentManager):
    index = ELASTICSEARCH_MEDIA_INDEX
    document = MediaDocument
    model = None

    @classmethod
    def create_index_document(cls, instance):
        """Returns a MediaDocument populated for the given media instance."""

        # Handle the case where the media instance has no original file
        if instance.original:
            instance_filename = instance.original.content.name
        else:
            instance_filename = None

        return cls.document(
            document_id=str(instance.id),
            document_type=type(instance).__name__,
            site_id=str(instance.site.id),
            site_visibility=instance.site.visibility,
            site_features=list(
                instance.site.sitefeature_set.filter(is_enabled=True).values_list(
                    "key", flat=True
                )
            ),
            visibility=Visibility.PUBLIC,
            title=instance.title,
            filename=instance_filename,
            description=instance.description,
            type=type(instance).__name__.lower(),
            exclude_from_games=instance.exclude_from_games,
            exclude_from_kids=instance.exclude_from_kids,
            created=instance.created,
            last_modified=instance.last_modified,
        )


class AudioDocumentManager(MediaDocumentManager):
    model = Audio

    @classmethod
    def create_index_document(cls, instance):
        document = super().create_index_document(instance)
        document.speakers = list(
            map(str, instance.speakers.values_list("id", flat=True))
        )
        return document


class DocumentDocumentManager(MediaDocumentManager):
    model = Document


class ImageDocumentManager(MediaDocumentManager):
    model = Image


class VideoDocumentManager(MediaDocumentManager):
    model = Video


class MediaIndexManager(IndexManager):
    index = ELASTICSEARCH_MEDIA_INDEX
    document_managers = [
        VideoDocumentManager,
        ImageDocumentManager,
        DocumentDocumentManager,
        AudioDocumentManager,
    ]
