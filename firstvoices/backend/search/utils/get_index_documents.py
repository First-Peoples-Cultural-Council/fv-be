from backend.search.documents import SongDocument, StoryDocument


def create_story_index_document(instance, page_text, page_translation):
    return StoryDocument(
        document_id=str(instance.id),
        site_id=str(instance.site.id),
        site_visibility=instance.site.visibility,
        exclude_from_games=instance.exclude_from_games,
        exclude_from_kids=instance.exclude_from_kids,
        visibility=instance.visibility,
        title=instance.title,
        title_translation=instance.title_translation,
        note=instance.notes,
        acknowledgement=instance.acknowledgements,
        introduction=instance.introduction,
        introduction_translation=instance.introduction_translation,
        author=instance.author,
        page_text=page_text,
        page_translation=page_translation,
        has_audio=instance.related_audio.exists(),
        has_video=instance.related_videos.exists(),
        has_image=instance.related_images.exists(),
        created=instance.created,
        last_modified=instance.last_modified,
    )


def create_song_index_document(instance, lyrics_text, lyrics_translation_text):
    return SongDocument(
        document_id=str(instance.id),
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
        lyrics_text=lyrics_text,
        lyrics_translation=lyrics_translation_text,
        has_audio=instance.related_audio.exists(),
        has_video=instance.related_videos.exists(),
        has_image=instance.related_images.exists(),
        created=instance.created,
        last_modified=instance.last_modified,
    )
