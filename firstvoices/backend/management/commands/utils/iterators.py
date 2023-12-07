import logging

from backend.models import DictionaryEntry, Song, Story
from backend.models.constants import Visibility
from backend.models.media import Audio, Image, Video
from backend.search.documents import DictionaryEntryDocument, MediaDocument
from backend.search.utils.constants import UNKNOWN_CHARACTER_FLAG
from backend.search.utils.get_index_documents import (
    create_song_index_document,
    create_story_index_document,
)
from backend.search.utils.object_utils import (
    get_acknowledgements_text,
    get_categories_ids,
    get_lyrics,
    get_notes_text,
    get_page_info,
    get_translation_text,
)


def media_doc_generator(instance, media_type):
    return MediaDocument(
        document_id=str(instance.id),
        site_id=str(instance.site.id),
        site_visibility=instance.site.visibility,
        exclude_from_games=instance.exclude_from_games,
        exclude_from_kids=instance.exclude_from_kids,
        visibility=Visibility.PUBLIC,
        title=instance.title,
        type=media_type,
        filename=instance.original.content.name,
        description=instance.description,
        created=instance.created,
        last_modified=instance.last_modified,
    )


def audio_iterator():
    logger = logging.getLogger("rebuild_index")

    queryset = Audio.objects.all()
    for instance in queryset:
        try:
            yield media_doc_generator(instance, "audio").to_dict(True)
        except AttributeError:
            logger.warning(
                f"Skipping document due to missing properties. object: audio, id: {instance.id}."
            )
            continue


def image_iterator():
    logger = logging.getLogger("rebuild_index")

    queryset = Image.objects.all()
    for instance in queryset:
        try:
            yield media_doc_generator(instance, "image").to_dict(True)
        except AttributeError:
            logger.warning(
                f"Skipping document due to missing properties. object: image, id: {instance.id}."
            )
            continue


def video_iterator():
    logger = logging.getLogger("rebuild_index")

    queryset = Video.objects.all()
    for instance in queryset:
        try:
            yield media_doc_generator(instance, "video").to_dict(True)
        except AttributeError:
            logger.warning(
                f"Skipping document due to missing properties. object: video, id: {instance.id}."
            )
            continue


def story_iterator():
    queryset = Story.objects.all()
    for instance in queryset:
        page_text, page_translation = get_page_info(instance)
        story_doc = create_story_index_document(instance, page_text, page_translation)
        yield story_doc.to_dict(True)


def dictionary_entry_iterator():
    queryset = DictionaryEntry.objects.all()
    for entry in queryset:
        translations_text = get_translation_text(entry)
        notes_text = get_notes_text(entry)
        acknowledgements_text = get_acknowledgements_text(entry)
        categories = get_categories_ids(entry)

        index_entry = DictionaryEntryDocument(
            document_id=str(entry.id),
            site_id=str(entry.site.id),
            site_visibility=entry.site.visibility,
            title=entry.title,
            type=entry.type,
            translation=translations_text,
            acknowledgement=acknowledgements_text,
            note=notes_text,
            categories=categories,
            exclude_from_kids=entry.exclude_from_kids,
            exclude_from_games=entry.exclude_from_games,
            custom_order=entry.custom_order,
            visibility=entry.visibility,
            has_audio=entry.related_audio.exists(),
            has_video=entry.related_videos.exists(),
            has_image=entry.related_images.exists(),
            created=entry.created,
            last_modified=entry.last_modified,
            has_translation=entry.translation_set.count() > 0,
            has_unrecognized_chars=UNKNOWN_CHARACTER_FLAG in entry.custom_order,
        )
        yield index_entry.to_dict(True)


def song_iterator():
    queryset = Song.objects.all()
    for instance in queryset:
        lyrics_text, lyrics_translation_text = get_lyrics(instance)
        song_doc = create_song_index_document(
            instance, lyrics_text, lyrics_translation_text
        )
        yield song_doc.to_dict(True)
