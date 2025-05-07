from rest_framework_csv import renderers


class BatchExportCSVRenderer(renderers.PaginatedCSVRenderer):
    """
    Sets our standard CSV columns and header labels for dictionary entry CSV responses.
    """

    header = [
        "id",
        "title",
        "type",
        "visibility",
        "translations.0.text",
        "translations.1.text",
        "translations.2.text",
        "translations.3.text",
        "translations.4.text",
        "acknowledgements.0.text",
        "alternate_spellings.0.text",
        "exclude_from_games",
        "exclude_from_kids",
        "is_immersion_label",
        "notes.0.text",
        "part_of_speech.title",
        "pronunciations.0.text",
        "related_audio.0.title",
        "related_audio.0.description",
        "related_audio.0.speakers.0.name",
        "related_audio.0.speakers.1.name",
        "related_audio.1.title",
        "related_audio.1.speakers.0.name",
        "site.slug",
        "created",
        "created_by",
        "last_modified",
        "last_modified_by",
    ]
    labels = {
        "acknowledgements.0.text": "acknowledgement",
        "alternate_spellings.0.text": "alternate_spelling",
        "notes.0.text": "note",
        "part_of_speech.title": "part_of_speech",
        "pronunciations.0.text": "pronunciation",
        "translations.0.text": "translation",
        "translations.1.text": "translation_2",
        "translations.2.text": "translation_3",
        "translations.3.text": "translation_4",
        "translations.4.text": "translation_5",
        "site.slug": "site_slug",
        "related_audio.0.title": "audio_title",
        "related_audio.0.description": "audio_description",
        "related_audio.0.speakers.0.name": "audio_speaker",
        "related_audio.0.speakers.1.name": "audio_speaker_2",
        "related_audio.1.title": "audio_2_title",
        "related_audio.1.speakers.0.name": "audio_2_speaker",
    }
