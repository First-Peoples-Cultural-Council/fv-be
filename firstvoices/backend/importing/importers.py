import tablib

from backend.models import ImportJob
from backend.resources.dictionary import DictionaryEntryResource
from backend.resources.media import AudioResource, ImageResource, VideoResource


class BaseImporter:
    resource = None
    supported_columns = []
    key_col = None

    @classmethod
    def get_supported_columns(cls):
        return cls.supported_columns

    @classmethod
    def import_data(cls, import_job: ImportJob, csv_data: str, dry_run: bool = True):
        raise NotImplementedError

    @classmethod
    def get_key_col(cls):
        return cls.key_col

    @classmethod
    def filter_data(cls, data):
        key_col = cls.get_key_col()
        filtered_data = cls.filter_columns(data, key_col)
        filtered_data = cls.filter_rows(filtered_data, key_col)

        return filtered_data

    @classmethod
    def filter_columns(cls, data, key_col=None):
        """
        Return only the allowed columns of data.
        """
        columns = [col for col in cls.get_supported_columns() if col in data.headers]
        filtered_data = tablib.Dataset(headers=columns)

        if key_col and key_col not in data.headers:
            return filtered_data

        for row in data.dict:
            row_values = [row[col] for col in columns]
            filtered_data.append(row_values)

        return filtered_data

    @classmethod
    def filter_rows(cls, data, filename_key):
        """Subclasses can override to filter out duplicate or invalid rows."""
        return data


class BaseMediaFileImporter(BaseImporter):
    column_prefix = ""

    @classmethod
    def get_key_col(cls):
        return f"{cls.column_prefix}_filename"

    @classmethod
    def filter_rows(cls, data, filename_key):
        """
        Removes rows with missing or duplicate filename. Only keeps the first row if multiple rows have same filenames.
        """
        seen_filenames = set()
        non_duplicated_data = tablib.Dataset(headers=data.headers)

        for row in data.dict:
            filename = row[filename_key]

            if not filename:
                continue

            if filename not in seen_filenames:
                seen_filenames.add(filename)
                non_duplicated_data.append(row.values())

        return non_duplicated_data

    @classmethod
    def import_data(cls, import_job: ImportJob, csv_data: str, dry_run: bool = True):
        """
        Imports media files listed the given csv data file, and returns import results along with
        a map of filenames to imported File ids.
        """
        filtered_data = cls.filter_data(csv_data)

        import_result = cls.resource(
            site=import_job.site,
            run_as_user=import_job.run_as_user,
            import_job=import_job.id,
        ).import_data(dataset=filtered_data, dry_run=dry_run)

        filename_map = {}

        if import_result.totals["new"]:
            for row in filtered_data.dict:
                filename = row[f"{cls.column_prefix}_filename"]
                filename_map[filename] = row["id"]

        return import_result, filename_map


class AudioImporter(BaseMediaFileImporter):
    resource = AudioResource
    column_prefix = "audio"
    supported_columns = [
        "audio_filename",
        "audio_title",
        "audio_description",
        "audio_speaker",
        "audio_speaker_2",
        "audio_speaker_3",
        "audio_speaker_4",
        "audio_speaker_5",
        "audio_acknowledgement",
        "audio_include_in_kids_site",
        "audio_include_in_games",
    ]


class ImageImporter(BaseMediaFileImporter):
    resource = ImageResource
    column_prefix = "img"
    supported_columns = [
        "img_filename",
        "img_title",
        "img_description",
        "img_acknowledgement",
        "img_include_in_kids_site",
    ]


class VideoImporter(BaseMediaFileImporter):
    resource = VideoResource
    column_prefix = "video"
    supported_columns = [
        "video_filename",
        "video_title",
        "video_description",
        "video_acknowledgement",
        "video_include_in_kids_site",
    ]


class DictionaryEntryImporter(BaseImporter):
    resource = DictionaryEntryResource
    supported_columns_single = [
        "title",
        "type",
        "visibility",
        "include_on_kids_site",
        "include_in_games",
    ]
    supported_columns_multiple = [
        "translation",
        "category",
        "note",
        "acknowledgement",
        "part_of_speech",
        "pronunciation",
        "alternate_spelling",
        "related_entry",
    ]
    supported_columns_media = [
        "audio_filename",
        "img_filename",
        "video_filename",
    ]

    @classmethod
    def get_supported_columns(cls):
        return (
            cls.supported_columns_single
            + cls.get_multiplied_columns()
            + cls.supported_columns_media
        )

    @classmethod
    def get_multiplied_columns(cls):
        target_columns = []

        for col in cls.supported_columns_multiple:
            target_columns.append(col)

            for i in range(2, 6):
                target_columns.append(f"{col}_{i}")

        return target_columns
