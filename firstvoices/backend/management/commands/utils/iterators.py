from backend.models import DictionaryEntry
from backend.search.documents import DictionaryEntryDocument
from backend.search.utils.constants import UNKNOWN_CHARACTER_FLAG
from backend.search.utils.object_utils import (
    get_acknowledgements_text,
    get_categories_ids,
    get_notes_text,
    get_translation_text,
)


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
