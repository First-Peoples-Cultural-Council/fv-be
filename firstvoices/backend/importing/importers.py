from backend.models import ImportJob
from backend.resources.media import AudioResource, ImageResource, VideoResource


class BaseMediaFileImporter:
    resource = None
    column_prefix = ""

    @classmethod
    def import_data(cls, import_job: ImportJob, data, dry_run: bool = True):
        """
        Imports media files listed the given csv data file, and returns import results along with
        a map of filenames to imported File ids.
        """
        import_result = cls.resource(
            site=import_job.site,
            run_as_user=import_job.run_as_user,
            import_job=import_job.id,
        ).import_data(dataset=data, dry_run=dry_run)

        filename_map = {}

        if import_result.totals["new"]:
            for row in data.dict:
                filename = row[f"{cls.column_prefix}_filename"]
                filename_map[filename] = row["id"]

        return import_result, filename_map


class AudioImporter(BaseMediaFileImporter):
    resource = AudioResource
    column_prefix = "audio"


class ImageImporter(BaseMediaFileImporter):
    resource = ImageResource
    column_prefix = "img"


class VideoImporter(BaseMediaFileImporter):
    resource = VideoResource
    column_prefix = "video"
