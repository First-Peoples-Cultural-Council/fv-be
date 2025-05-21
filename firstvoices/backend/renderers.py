from rest_framework_csv import renderers


class BatchExportCSVRenderer(renderers.PaginatedCSVRenderer):
    """
    Sets our standard CSV columns and header labels for dictionary entry CSV responses.
    """

    def __init__(self):
        self.header = (
            ["id", "title", "type", "visibility"]
            + self._get_text_list("alternate_spellings")
            + self._get_text_list("translations")
            + self._get_text_list("pronunciations")
            + self._get_text_list("acknowledgements")
            + self._get_text_list("notes")
            + ["exclude_from_games", "exclude_from_kids", "part_of_speech.title"]
            + self._get_audio_list()
            + self._get_media_list("related_images")
            + self._get_media_list("related_videos")
            + [
                "site.slug",
                "created",
                "created_by",
                "last_modified",
                "last_modified_by",
            ]
        )

        self.labels = {
            "part_of_speech.title": "part_of_speech",
            "site.slug": "site_slug",
            **self._get_text_list_labels("translations", "translation"),
            **self._get_text_list_labels("alternate_spellings", "alternate_spelling"),
            **self._get_text_list_labels("notes", "note"),
            **self._get_text_list_labels("pronunciations", "pronunciation"),
            **self._get_text_list_labels("acknowledgements", "acknowledgement"),
            **self._get_audio_list_labels(),
            **self._get_media_list_labels("related_images", "img"),
            **self._get_media_list_labels("related_videos", "video"),
        }

    def _get_text_list(self, key):
        return [f"{key}.{i}.text" for i in range(0, 5)]

    def _get_text_list_labels(self, key, label):
        labels = {}
        for i in range(0, 5):
            suffix = f"_{i+1}" if i > 0 else ""
            labels.update({f"{key}.{i}.text": f"{label}{suffix}"})

        return labels

    def _get_audio_list(self):
        headers = []

        for i in range(0, 5):
            headers += self._get_media_headers("related_audio", i)

            for j in range(0, 5):
                headers.append(f"related_audio.{i}.speakers.{j}.name")

        return headers

    def _get_media_list(self, key):
        headers = []

        for i in range(0, 5):
            headers += self._get_media_headers(key, i)

        return headers

    def _get_media_headers(self, key, i):
        headers = []
        media_columns = [
            "original.path",
            "title",
            "description",
            "acknowledgement",
            "exclude_from_kids",
            "exclude_from_games",
        ]

        for field in media_columns:
            headers.append(f"{key}.{i}.{field}")

        return headers

    def _get_audio_list_labels(self):
        labels = {}
        header_prefix = "related_audio"
        label_prefix = "audio"

        for i in range(0, 5):
            item_labels, prefix = self._get_media_labels(i, header_prefix, label_prefix)
            labels.update(item_labels)

            for j in range(0, 5):
                if j == 0:
                    speaker = "speaker"
                else:
                    speaker = f"speaker_{j+1}"

                labels.update(
                    {f"{header_prefix}.{i}.speakers.{j}.name": f"{prefix}{speaker}"}
                )

        return labels

    def _get_media_list_labels(self, header_prefix, label_prefix):
        labels = {}

        for i in range(0, 5):
            item_labels, _ = self._get_media_labels(i, header_prefix, label_prefix)
            labels.update(item_labels)

        return labels

    def _get_media_labels(self, i, header_prefix, label_prefix):
        labels = {}
        media_field_labels = {
            "original.path": "filename",
            "title": "title",
            "description": "description",
            "acknowledgement": "acknowledgement",
            "exclude_from_kids": "exclude_from_kids_site",
            "exclude_from_games": "exclude_from_games",
        }

        for field, label in media_field_labels.items():
            if i == 0:
                prefix = f"{label_prefix}_"
            else:
                prefix = f"{label_prefix}_{i + 1}_"

            labels.update({f"{header_prefix}.{i}.{field}": f"{prefix}{label}"})

        return labels, prefix
