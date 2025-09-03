import tablib

# Mapping to handle plural forms, capitalization and such
FIELD_MAP = {
    "id": "ID",
    "title": "TITLE",
    "type": "TYPE",
    "translations": "TRANSLATION",
    "notes": "NOTE",
    "acknowledgements": "ACKNOWLEDGEMENT",
    "alternate_spellings": "ALTERNATE_SPELLING",
    "pronunciations": "PRONUNCIATION",
    "categories": "CATEGORY",
    "visibility": "VISIBILITY",
    "part_of_speech": "PART_OF_SPEECH",
    "include_in_games": "INCLUDE_IN_GAMES",
    "include_on_kids_site": "INCLUDE_ON_KIDS_SITE",
    "image_ids": "IMAGE_IDS",
    "audio_ids": "AUDIO_IDS",
    "video_ids": "VIDEO_IDS",
    "related_video_links": "VIDEO_EMBED_LINK",
    "related_dictionary_entries": "RELATED_ENTRY_ID",
}

BOOLEAN_INVERT_FIELDS = {
    "exclude_from_games": "include_in_games",
    "exclude_from_kids": "include_on_kids_site",
}

MEDIA_FIELDS = {
    "related_images": "image_ids",
    "related_audio": "audio_ids",
    "related_videos": "video_ids",
}


def get_dataset_from_queryset(queryset):
    # Convert to CSV
    fields = [
        "id",
        "title",
        "type",
        "translations",
        "categories",
        "visibility",
        "part_of_speech",
        "related_video_links",
        "notes",
        "acknowledgements",
        "alternate_spellings",
        "pronunciations",
        "related_dictionary_entries",
        *BOOLEAN_INVERT_FIELDS.keys(),
        *MEDIA_FIELDS.keys(),
    ]

    headers = [
        BOOLEAN_INVERT_FIELDS.get(field) or MEDIA_FIELDS.get(field) or field
        for field in fields
    ]
    data = []

    for entry in queryset:
        row = []
        for field in fields:
            # Media fields generates comma separated list
            if field in MEDIA_FIELDS.keys():
                ids = getattr(entry, field).values_list("id", flat=True)
                row.append(",".join(map(str, ids)))

            elif field == "categories":
                values = getattr(entry, field).all()
                row.append([str(value) for value in values])

            elif field == "related_dictionary_entries":
                ids = getattr(entry, field).values_list("id", flat=True)
                row.append([str(id) for id in ids])

            else:
                value = getattr(entry, field)

                # field with choices
                if hasattr(entry, f"get_{field}_display"):
                    value = getattr(entry, f"get_{field}_display")()

                # invert booleans
                if field in ["exclude_from_games", "exclude_from_kids"]:
                    value = not bool(value)

                row.append(value)

        data.append(row)
    return tablib.Dataset(*data, headers=headers)


def expand_many_to_one(dataset, field_name, max_columns=None):
    if field_name not in dataset.headers:
        return dataset

    field_index = dataset.headers.index(field_name)

    # determine max columns
    actual_max = 0
    for row in dataset.dict:
        value = row.get(field_name, [])
        if isinstance(value, (list, tuple)):
            actual_max = max(actual_max, len(value))
        elif value:
            actual_max = max(actual_max, 1)
    num_columns = actual_max if max_columns is None else min(actual_max, max_columns)

    new_headers = (
        dataset.headers[:field_index]
        + [
            field_name if i == 0 else f"{field_name}_{i + 1}"
            for i in range(num_columns)
        ]
        + dataset.headers[field_index + 1 :]  # noqa: E203
    )

    # build new rows
    new_data = []
    for row in dataset.dict:
        values = row.get(field_name, [])
        if not isinstance(values, (list, tuple)):
            values = [values] if values else []

        expanded_values = [
            values[i] if i < len(values) else "" for i in range(num_columns)
        ]

        before = [row[h] for h in dataset.headers[:field_index]]
        after = [row[h] for h in dataset.headers[field_index + 1 :]]  # noqa: E203
        new_row = before + expanded_values + after
        new_data.append(new_row)

    return tablib.Dataset(*new_data, headers=new_headers)
