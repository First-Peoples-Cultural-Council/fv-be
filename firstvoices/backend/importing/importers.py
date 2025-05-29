import tablib

from backend.models import ImportJob
from backend.resources.media import AudioResource, ImageResource, VideoResource


class BaseMediaFileImporter:
    resource = None
    column_prefix = ""
    supported_columns = []

    @classmethod
    def filter_data(cls, data):
        filename_col = f"{cls.column_prefix}_filename"
        filtered_data = cls.filter_columns(data, filename_col)
        filtered_data = cls.remove_duplicate_rows(filtered_data, filename_col)

        return filtered_data

    @classmethod
    def filter_columns(cls, data, filename_key):
        """
        Helper function to build filtered media datasets
        """
        columns = [col for col in cls.supported_columns if col in data.headers]
        raw_data = tablib.Dataset(headers=columns)
        filtered_data = tablib.Dataset(headers=columns)
        if filename_key in data.headers:
            for row in data.dict:
                row_values = [row[col] for col in columns]
                raw_data.append(row_values)
                if row.get(filename_key):
                    filtered_data.append(row_values)
        return filtered_data

    @classmethod
    def remove_duplicate_rows(cls, data, filename_key):
        """
        Only keep the first row if multiple rows have same filenames.
        """
        seen_filenames = set()
        non_duplicated_data = tablib.Dataset(headers=data.headers)

        for row in data.dict:
            filename = row[filename_key]
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
