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
from backend.resources.base import SiteContentResource
from backend.resources.utils.import_export_widgets import (
    CustomManyToManyWidget,
    InvertedBooleanFieldWidget,
)


class BaseMediaResource(SiteContentResource):
    def before_import(self, dataset, **kwargs):
        super().before_import(dataset, **kwargs)

        # Adding "id" column if in update mode,
        # since media is always imported and not updated
        import_job = ImportJob.objects.get(id=self.import_job)
        if import_job.mode == ImportJobMode.UPDATE:
            dataset.append_col(lambda x: str(uuid.uuid4()), header="id")


class AudioResource(BaseMediaResource):
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
        associated_file = File.objects.filter(
            import_job__id=row["import_job"], content__contains=valid_filename
        )[0]
        row["audio_original"] = str(associated_file.id)

    class Meta:
        model = Audio
        clean_model_instances = True


class DocumentResource(BaseMediaResource):
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
        associated_file = File.objects.filter(
            import_job__id=row["import_job"], content__contains=valid_filename
        )[0]
        row["document_original"] = str(associated_file.id)

    class Meta:
        model = Document
        clean_model_instances = True


class ImageResource(BaseMediaResource):
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
        associated_file = ImageFile.objects.filter(
            import_job__id=row["import_job"], content__contains=valid_filename
        )[0]
        row["img_original"] = str(associated_file.id)

    class Meta:
        model = Image
        clean_model_instances = True


class VideoResource(BaseMediaResource):
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
        associated_file = VideoFile.objects.filter(
            import_job__id=row["import_job"], content__contains=valid_filename
        )[0]
        row["video_original"] = str(associated_file.id)

    class Meta:
        model = Video
        clean_model_instances = True
