import re

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
    def filter_rows(cls, data, key_col):
        """Subclasses can override to filter out duplicate or invalid rows."""
        return data


class BaseMediaFileImporter(BaseImporter):
    column_prefix = ""

    supported_column_suffixes = [
        "filename",
        "title",
        "description",
        "acknowledgement",
        "include_in_kids_site",
    ]

    @classmethod
    def get_key_col(cls):
        return f"{cls.column_prefix}_filename"

    @classmethod
    def get_supported_columns(cls):
        """
        Returns a list of supported columns for the media file importer.
        Uses column prefix, supported suffixes, and multiplies them to create the full list.
        """
        columns = []
        for suffix in cls.supported_column_suffixes:
            columns.append(f"{cls.column_prefix}_{suffix}")

            for i in range(2, 6):
                columns.append(f"{cls.column_prefix}_{i}_{suffix}")

        return columns

    @classmethod
    def filter_rows(cls, data, filename_key):
        """
        Removes rows with missing or duplicate filename. Only keeps the first row if multiple rows have same filenames.
        """
        seen_filenames = set()
        non_duplicated_data = tablib.Dataset(headers=data.headers)

        filename_columns = [
            col for col in cls.get_supported_columns() if col.endswith("filename")
        ]

        for row in data.dict:
            primary_filename = row[filename_key]

            if not primary_filename:
                continue

            row_filenames = [row[col] for col in filename_columns if col in row]

            for filename in row_filenames:
                if filename not in seen_filenames:
                    seen_filenames.add(filename)
                    non_duplicated_data.append(row.values())

        return non_duplicated_data

    @classmethod
    def split_file_data(cls, data):
        """
        Splits file data into separate datasets based on column number.
        Returns a list of datasets, each containing a single file's data for import.
        """
        datasets = []
        headers = data.headers

        # if data is empty, return an empty list
        if not headers:
            return datasets

        # if column name includes _\d_ and \d is the same digit, then it is the data of the same file
        for i in range(1, 6):
            # Build regex pattern for the i-th file group
            if i == 1:
                pattern = (
                    rf"^{cls.column_prefix}_[a-z]+(?:_[a-z]+)*(_[2-5])?$"  # noqa: E231
                )
            else:
                pattern = rf"^{cls.column_prefix}_{i}_[a-z]+(?:_[a-z]+)*(_[2-5])?$"  # noqa: E231

            file_columns = [
                col for col in headers if re.match(pattern, col, re.IGNORECASE)
            ]

            if not file_columns:
                continue

            file_data = tablib.Dataset(headers=file_columns)
            for row in data.dict:
                row_values = [row[col] for col in file_columns]
                file_data.append(row_values)
            datasets.append(file_data)

        return datasets

    @classmethod
    def import_data(cls, import_job: ImportJob, csv_data: str, dry_run: bool = True):
        """
        Imports media files listed the given csv data file, and returns import results along with
        a map of filenames to imported File ids.
        """

        # Split the data into separate datasets for each file
        split_file_data = cls.split_file_data(csv_data)

        import_results = []
        filename_map = {}

        for dataset in split_file_data:
            # replace numbered prefixes with the base prefix
            dataset.headers = [
                re.sub(rf"^{cls.column_prefix}_\d_", f"{cls.column_prefix}_", col)
                for col in dataset.headers
            ]

            # filter out duplicate and empty filenames
            dataset = cls.filter_rows(dataset, cls.get_key_col())

            import_result = cls.resource(
                site=import_job.site,
                run_as_user=import_job.run_as_user,
                import_job=import_job.id,
            ).import_data(dataset=dataset, dry_run=dry_run)

            if import_result.totals["new"]:
                for i, row in enumerate(dataset.dict):
                    filename = row[f"{cls.column_prefix}_filename"]
                    # for the filename map, store  (row_index, file_id)
                    filename_map[filename] = (i, row["id"])

            import_results.append(import_result)

        return import_results, filename_map


class AudioImporter(BaseMediaFileImporter):
    resource = AudioResource
    column_prefix = "audio"

    @classmethod
    def get_supported_columns(cls):
        speaker_columns = []
        for i in range(1, 6):
            if i == 1:
                speaker_columns.append(f"{cls.column_prefix}_include_in_games")
            else:
                speaker_columns.append(f"{cls.column_prefix}_{i}_include_in_games")

            for j in range(1, 6):
                if i == 1 and j == 1:
                    speaker_columns.append(f"{cls.column_prefix}_speaker")
                elif i == 1:
                    speaker_columns.append(f"{cls.column_prefix}_speaker_{j}")
                elif j == 1:
                    speaker_columns.append(f"{cls.column_prefix}_{i}_speaker")
                else:
                    speaker_columns.append(f"{cls.column_prefix}_{i}_speaker_{j}")

        return super().get_supported_columns() + speaker_columns


class ImageImporter(BaseMediaFileImporter):
    resource = ImageResource
    column_prefix = "img"


class VideoImporter(BaseMediaFileImporter):
    resource = VideoResource
    column_prefix = "video"


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

        # get the row index for the current row (from primary filename)
        primary_filename = row_list[filename_col_index]
        if not primary_filename:
            return

        filename_row_idx = media_map[primary_filename][0]

        # get the related media ids from the map
        related_file_ids = [
            file_id
            for (row_index, file_id) in media_map.values()
            if row_index == filename_row_idx
        ]

        # update related media with a comma-separated string of related ids
        row_list[related_media_col_index] = ",".join(
            [str(file_id) for file_id in related_file_ids if file_id]
        )
