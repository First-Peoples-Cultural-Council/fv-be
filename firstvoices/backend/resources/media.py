import uuid

from django.utils.text import get_valid_filename
from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models.files import File
from backend.models.import_jobs import ImportJob, ImportJobMode
from backend.models.media import (
    Audio,
    Document,
    Image,
    ImageFile,
    Person,
    Video,
    VideoFile,
)
from backend.models.update_jobs import UpdateJob
from backend.resources.base import SiteContentResource
from backend.resources.utils.import_export_widgets import (
    CustomManyToManyWidget,
    InvertedBooleanFieldWidget,
)


class BaseMediaResource(SiteContentResource):
    original_column_name = None

    def get_related_job_filter(self, row):
        if row.get("import_job"):
            return {"import_job__id": row["import_job"]}

        update_job_id = row.get("update_job")
        if not update_job_id:
            update_job_id = (
                self.update_job.id
                if isinstance(self.update_job, UpdateJob)
                else self.update_job
            )

        return {"update_job__id": str(update_job_id)}

    def before_import(self, dataset, **kwargs):
        super().before_import(dataset, **kwargs)

        # Adding "id" column if in update mode,
        # since media is always imported and not updated
        is_update_mode = isinstance(self.job, UpdateJob) or (
            isinstance(self.job, ImportJob) and self.job.mode == ImportJobMode.UPDATE
        )
        if is_update_mode:
            dataset.append_col(lambda x: str(uuid.uuid4()), header="id")

    def import_row(self, row, instance_loader, **kwargs):
        result = super().import_row(row, instance_loader, **kwargs)

        original_row_number = row.get("_row_number")
        if original_row_number:
            result.number = int(original_row_number)

        return result

    def skip_row(self, instance, original, row, import_validation_errors=None) -> bool:
        # skip rows with missing originals (errors will be logged in DictionaryEntryResource)
        # skipped rows with no error message will not appear in error report
        if not row.get(self.original_column_name):
            return True
        return super().skip_row(instance, original, row, import_validation_errors)


class AudioResource(BaseMediaResource):
    original_column_name = "audio_original"

    original = fields.Field(
        column_name="audio_original",
        attribute="original",
        widget=ForeignKeyWidget(model=File),
    )

    title = fields.Field(
        column_name="audio_title",
        attribute="title",
    )

    description = fields.Field(column_name="audio_description", attribute="description")

    acknowledgement = fields.Field(
        column_name="audio_acknowledgement", attribute="acknowledgement"
    )

    speakers = fields.Field(
        column_name="audio_speaker",
        attribute="speakers",
        m2m_add=True,
        widget=CustomManyToManyWidget(
            model=Person, field="name", column_name="audio_speaker"
        ),
    )

    exclude_from_games = fields.Field(
        column_name="audio_include_in_games",
        attribute="exclude_from_games",
        widget=InvertedBooleanFieldWidget(
            column="audio_include_in_games", default=False
        ),
    )

    exclude_from_kids = fields.Field(
        column_name="audio_include_in_kids_site",
        attribute="exclude_from_kids",
        widget=InvertedBooleanFieldWidget(
            column="audio_include_in_kids_site", default=False
        ),
    )

    def before_import_row(self, row, **kwargs):
        # Filename to be used as title if not provided
        if "audio_title" not in row or len(row["audio_title"]) == 0:
            row["audio_title"] = row["audio_filename"]

        valid_filename = get_valid_filename(row["audio_filename"])

        # Adding original
        related_job_filter = self.get_related_job_filter(row)
        associated_file = File.objects.filter(
            content__contains=valid_filename, **related_job_filter
        ).first()
        if associated_file:
            row["audio_original"] = str(associated_file.id)

    class Meta:
        model = Audio
        clean_model_instances = True


class DocumentResource(BaseMediaResource):
    original_column_name = "document_original"

    original = fields.Field(
        column_name="document_original",
        attribute="original",
        widget=ForeignKeyWidget(model=File),
    )

    title = fields.Field(
        column_name="document_title",
        attribute="title",
    )

    description = fields.Field(
        column_name="document_description", attribute="description"
    )

    acknowledgement = fields.Field(
        column_name="document_acknowledgement", attribute="acknowledgement"
    )

    exclude_from_kids = fields.Field(
        column_name="document_include_in_kids_site",
        attribute="exclude_from_kids",
        widget=InvertedBooleanFieldWidget(
            column="document_include_in_kids_site", default=False
        ),
    )

    def before_import_row(self, row, **kwargs):
        # Filename to be used as title if not provided
        if "document_title" not in row or len(row["document_title"]) == 0:
            row["document_title"] = row["document_filename"]

        valid_filename = get_valid_filename(row["document_filename"])

        # Adding original
        related_job_filter = self.get_related_job_filter(row)
        associated_file = File.objects.filter(
            content__contains=valid_filename, **related_job_filter
        ).first()
        if associated_file:
            row["document_original"] = str(associated_file.id)

    class Meta:
        model = Document
        clean_model_instances = True


class ImageResource(BaseMediaResource):
    original_column_name = "img_original"

    original = fields.Field(
        column_name="img_original",
        attribute="original",
        widget=ForeignKeyWidget(model=ImageFile),
    )

    title = fields.Field(
        column_name="img_title",
        attribute="title",
    )

    description = fields.Field(column_name="img_description", attribute="description")

    acknowledgement = fields.Field(
        column_name="img_acknowledgement", attribute="acknowledgement"
    )

    exclude_from_kids = fields.Field(
        column_name="img_include_in_kids_site",
        attribute="exclude_from_kids",
        widget=InvertedBooleanFieldWidget(
            column="img_include_in_kids_site", default=False
        ),
    )

    def before_import_row(self, row, **kwargs):
        # Filename to be used as title if not provided
        if "img_title" not in row or len(row["img_title"]) == 0:
            row["img_title"] = row["img_filename"]

        valid_filename = get_valid_filename(row["img_filename"])

        # Adding original
        related_job_filter = self.get_related_job_filter(row)
        associated_file = ImageFile.objects.filter(
            content__contains=valid_filename, **related_job_filter
        ).first()
        if associated_file:
            row["img_original"] = str(associated_file.id)

    class Meta:
        model = Image
        clean_model_instances = True


class VideoResource(BaseMediaResource):
    original_column_name = "video_original"

    original = fields.Field(
        column_name="video_original",
        attribute="original",
        widget=ForeignKeyWidget(model=VideoFile),
    )

    title = fields.Field(
        column_name="video_title",
        attribute="title",
    )

    description = fields.Field(column_name="video_description", attribute="description")

    acknowledgement = fields.Field(
        column_name="video_acknowledgement", attribute="acknowledgement"
    )

    exclude_from_kids = fields.Field(
        column_name="video_include_in_kids_site",
        attribute="exclude_from_kids",
        widget=InvertedBooleanFieldWidget(
            column="video_include_in_kids_site", default=False
        ),
    )

    def before_import_row(self, row, **kwargs):
        # Filename to be used as title if not provided
        if "video_title" not in row or len(row["video_title"]) == 0:
            row["video_title"] = row["video_filename"]

        valid_filename = get_valid_filename(row["video_filename"])

        # Adding original
        related_job_filter = self.get_related_job_filter(row)
        associated_file = VideoFile.objects.filter(
            content__contains=valid_filename, **related_job_filter
        ).first()
        if associated_file:
            row["video_original"] = str(associated_file.id)

    class Meta:
        model = Video
        clean_model_instances = True
