from backend.search.documents import StoryDocument


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
        has_document=instance.related_documents.exists(),
        has_image=instance.related_images.exists(),
        has_video=instance.related_videos.exists(),
        created=instance.created,
        last_modified=instance.last_modified,
        has_translation=bool(instance.title_translation),
    )


def text_as_list(comma_delimited_text):
    if comma_delimited_text is None:
        return comma_delimited_text

    items = comma_delimited_text.split(",")
    return [item.strip() for item in items]


def fields_as_list(queryset, field):
    values = queryset.values_list(field)
    return [str(x[0]) for x in values]
