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

        related_audio_column = cls.add_column(filtered_data, "related_audio")
        audio_filename_column = cls.get_column_index(filtered_data, "audio_filename")
        related_image_column = cls.add_column(filtered_data, "related_images")
        image_filename_column = cls.get_column_index(filtered_data, "img_filename")
        related_video_column = cls.add_column(filtered_data, "related_videos")
        video_filename_column = cls.get_column_index(filtered_data, "video_filename")

        for i, row in enumerate(filtered_data.dict):
            row_list = list(filtered_data[i])
            cls.add_related_id(
                row_list,
                audio_filename_column,
                related_audio_column,
                audio_filename_map,
            )
            cls.add_related_id(
                row_list, image_filename_column, related_image_column, img_filename_map
            )
            cls.add_related_id(
                row_list,
                video_filename_column,
                related_video_column,
                video_filename_map,
            )
            filtered_data[i] = tuple(row_list)

        dictionary_entry_import_result = DictionaryEntryResource(
            site=import_job.site,
            run_as_user=import_job.run_as_user,
            import_job=import_job.id,
        ).import_data(dataset=filtered_data, dry_run=dry_run)

        return dictionary_entry_import_result

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

    @classmethod
    def add_related_id(
        cls, row_list, filename_col_index, related_media_col_index, media_map
    ):
        """
        Lookup the filename in the media map, and add the id of the media resource to
        the provided row.
        """
        if not media_map:
            # If media map is empty, do nothing
            return

        filename = row_list[filename_col_index]
        related_id = media_map.get(filename, "")
        row_list[related_media_col_index] = related_id
