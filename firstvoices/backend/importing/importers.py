import tablib
from django.db.models import Q

from backend.models.import_jobs import ImportJob
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
    def get_referenced_id_col(cls):
        return f"{cls.column_prefix}_id"

    @classmethod
    def get_related_media_col(cls):
        return cls.related_column

    @classmethod
    def get_filename_map(cls, filtered_data: tablib.Dataset):
        return {
            row[f"{cls.column_prefix}_filename"]: row["id"]
            for row in filtered_data.dict
        }

    @classmethod
    def filter_rows(cls, data: tablib.Dataset, filename_key: str):
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
    def add_related_media_column(
        cls, site_id, data: tablib.Dataset, filename_map: dict
    ):
        """Adds a column containing the IDs of related media. If there are no related files, no column is added."""
        referenced_id_column_idx = cls.get_column_index(
            data, cls.get_referenced_id_col()
        )
        filename_column_idx = cls.get_column_index(data, cls.get_key_col())

        if (not filename_map) and (referenced_id_column_idx == -1):
            # No related media
            return data

        new_data = tablib.Dataset()
        new_data.headers = data.headers

        cls.add_column(new_data, cls.get_related_media_col())
        referenceable_media_ids = cls.get_referenceable_media_ids(site_id)

        for i, row in enumerate(data.dict):
            row_data = cls.append_related_ids(
                list(data[i]),
                filename_column_idx,
                filename_map,
                referenced_id_column_idx,
                referenceable_media_ids,
            )
            new_data.append(row_data)

        return new_data

    @classmethod
    def append_related_ids(
        cls,
        row_data: list,
        filename_column_idx: int,
        filename_map: dict,
        referenced_id_column_idx: int,
        referenceable_media_ids: list,
    ):
        imported_ids = cls.get_imported_ids(row_data, filename_column_idx, filename_map)
        referenced_ids = cls.get_referenced_ids(
            row_data, referenced_id_column_idx, referenceable_media_ids
        )
        all_related_ids = imported_ids + referenced_ids

        related_id_string = ",".join(all_related_ids)
        row_data.append(related_id_string)

        return tuple(row_data)

    @classmethod
    def get_imported_ids(
        cls, row_data: list, filename_column_idx: int, filename_map: dict
    ):
        if filename_column_idx < 0 or filename_map is None:
            return []

        filename = row_data[filename_column_idx]
        related_ids = []
        file_id = filename_map.get(filename, None)
        if file_id:
            related_ids.append(file_id)

        return related_ids

    @classmethod
    def get_column_index(cls, data: tablib.Dataset, column_name: str):
        """
        Return the index of column if present in the dataset.
        """
        try:
            column_index = data.headers.index(column_name)
            return column_index
        except ValueError:
            return -1

    @classmethod
    def add_column(cls, data: tablib.Dataset, column_name: str):
        """
        Add provided column to the tablib dataset.
        """
        data.append_col([""] * len(data), header=column_name)
        return data.headers.index(column_name)

    @classmethod
    def get_referenced_ids(
        cls, row_data: list, referenced_id_col_idx: int, referenceable_media_ids: list
    ):
        if referenced_id_col_idx < 0:
            return []

        ids = row_data[referenced_id_col_idx]
        if ids and ids in referenceable_media_ids:
            return [row_data[referenced_id_col_idx]]
        return []

    @classmethod
    def get_missing_referenced_media(cls, site_id, data):
        """Return a list of ids from data that do not correspond to media from the given site, or sites with
        shared media."""
        column_name = cls.get_referenced_id_col()
        valid_media_ids = cls.get_referenceable_media_ids(site_id)
        missing_media_ids = []

        clean_headers = [header.lower() for header in data.headers]

        if column_name.lower() in clean_headers:
            id_col_idx = clean_headers.index(column_name.lower())

            for idx, media_id in enumerate(data.get_col(id_col_idx)):
                if not media_id:
                    # Do nothing if the field is empty
                    continue
                if media_id not in valid_media_ids:
                    missing_media_ids.append({"idx": idx + 1, "id": media_id})

        return missing_media_ids

    @classmethod
    def get_referenceable_media_ids(cls, site_id):
        model = cls.resource.Meta.model
        sites_filter = Q(site=site_id) | Q(
            site__sitefeature_set__key__iexact="shared_media",
            site__sitefeature_set__is_enabled=True,
        )

        return [
            str(value)
            for value in model.objects.filter(sites_filter).values_list("id", flat=True)
        ]


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
        "external_system",
        "external_system_entry_id",
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
        "related_audio",
        "related_images",
        "related_videos",
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
        site_id = import_job.site.id
        data_with_audio = AudioImporter.add_related_media_column(
            site_id, csv_data, audio_filename_map
        )
        data_with_audio_and_images = ImageImporter.add_related_media_column(
            site_id, data_with_audio, img_filename_map
        )
        data_with_media = VideoImporter.add_related_media_column(
            site_id, data_with_audio_and_images, video_filename_map
        )

        filtered_data = cls.filter_data(data_with_media)

        dictionary_entry_import_result = DictionaryEntryResource(
            site=import_job.site,
            run_as_user=import_job.run_as_user,
            import_job=import_job.id,
        ).import_data(dataset=filtered_data, dry_run=dry_run)

        return dictionary_entry_import_result
