from backend.search.documents import SongDocument, StoryDocument


def get_new_story_index_document(instance, page_text, page_translation):
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
        hasAudio=instance.related_audio.exists(),
        hasVideo=instance.related_videos.exists(),
        hasImage=instance.related_images.exists(),
    )


def get_new_song_index_document(instance, lyrics_text, lyrics_translation_text):
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
        hasAudio=instance.related_audio.exists(),
        hasVideo=instance.related_videos.exists(),
        hasImage=instance.related_images.exists(),
    )
