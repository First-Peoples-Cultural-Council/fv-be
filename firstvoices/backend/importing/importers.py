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
    related_column = ""

    @classmethod
    def get_key_col(cls):
        return f"{cls.column_prefix}_filename"

    @classmethod
    def get_related_media_col(cls):
        return cls.related_column

    @classmethod
    def get_filename_map(cls, filtered_data):
        return {
            row[f"{cls.column_prefix}_filename"]: row["id"]
            for row in filtered_data.dict
        }

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

        if import_result.totals["new"]:
            return import_result, cls.get_filename_map(filtered_data)

        return import_result, {}

    @classmethod
    def add_related_media_column(cls, data, filename_map):
        """Adds a column containing the IDs of related media. If there are no related files, no column is added."""
        if not filename_map:
            # If map is empty, do nothing
            return data

        new_data = tablib.Dataset()
        new_data.headers = data.headers

        filename_column_idx = cls.get_column_index(new_data, cls.get_key_col())
        cls.add_column(new_data, cls.get_related_media_col())

        for i, row in enumerate(data.dict):
            row_data = cls.append_related_id(
                list(data[i]), filename_column_idx, filename_map
            )
            new_data.append(row_data)

        return new_data

    @classmethod
    def append_related_id(
        cls, row_data: list, filename_column_idx: int, filename_map: dict
    ):
        filename = row_data[filename_column_idx]
        related_id = filename_map.get(filename, "")
        row_data.append(related_id)
        return tuple(row_data)

    @classmethod
    def get_column_index(cls, data, column_name):
        """
        Return the index of column if present in the dataset.
        """
        try:
            column_index = data.headers.index(column_name)
            return column_index
        except ValueError:
            return -1

    @classmethod
    def add_column(cls, data, column_name):
        """
        Add provided column to the tablib dataset.
        """
        data.append_col([""] * len(data), header=column_name)
        return data.headers.index(column_name)


class AudioImporter(BaseMediaFileImporter):
    resource = AudioResource
    column_prefix = "audio"
    related_column = "related_audio"
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
        "audio_id",
    ]


class ImageImporter(BaseMediaFileImporter):
    resource = ImageResource
    column_prefix = "img"
    related_column = "related_images"
    supported_columns = [
        "img_filename",
        "img_title",
        "img_description",
        "img_acknowledgement",
        "img_include_in_kids_site",
        "img_id",
    ]


class VideoImporter(BaseMediaFileImporter):
    resource = VideoResource
    column_prefix = "video"
    related_column = "related_videos"
    supported_columns = [
        "video_filename",
        "video_title",
        "video_description",
        "video_acknowledgement",
        "video_include_in_kids_site",
        "video_id",
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

    @classmethod
    def import_data(
        cls,
        import_job,
        csv_data,
        dry_run,
        audio_filename_map,
        img_filename_map,
        video_filename_map,
    ):
        """
        Imports dictionary entries and returns the import result.
        This method adds related media columns, i.e. "related_images", "related_audio" and fills
        them up with ids from the media maps, by looking them up against the filename columns.
        """
        filtered_data = cls.filter_data(csv_data)

        data_with_audio = AudioImporter.add_related_media_column(
            filtered_data, audio_filename_map
        )
        data_with_images = ImageImporter.add_related_media_column(
            data_with_audio, img_filename_map
        )
        data_with_media = VideoImporter.add_related_media_column(
            data_with_images, video_filename_map
        )

        dictionary_entry_import_result = DictionaryEntryResource(
            site=import_job.site,
            run_as_user=import_job.run_as_user,
            import_job=import_job.id,
        ).import_data(dataset=data_with_media, dry_run=dry_run)

        return dictionary_entry_import_result
