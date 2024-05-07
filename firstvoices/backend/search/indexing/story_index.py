from backend.models import Story
from backend.search.documents import StoryDocument
from backend.search.indexing.base import DocumentManager, IndexManager
from backend.search.utils.constants import ELASTICSEARCH_STORY_INDEX
from backend.search.utils.get_index_documents import fields_as_list


class StoryDocumentManager(DocumentManager):
    index = ELASTICSEARCH_STORY_INDEX
    document = StoryDocument
    model = Story

    @classmethod
    def create_index_document(cls, instance: Story):
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
            page_text=fields_as_list(instance.pages, "text"),
            page_translation=fields_as_list(instance.pages, "translation"),
            author=instance.author,
            note=instance.notes,
            acknowledgement=instance.acknowledgements,
            has_audio=instance.related_audio.exists(),
            has_video=instance.related_videos.exists()
            or bool(instance.related_video_links),
            has_image=instance.related_images.exists(),
            exclude_from_games=instance.exclude_from_games,
            exclude_from_kids=instance.exclude_from_kids,
            created=instance.created,
            last_modified=instance.last_modified,
        )


class StoryIndexManager(IndexManager):
    index = ELASTICSEARCH_STORY_INDEX
    document_managers = [StoryDocumentManager]
