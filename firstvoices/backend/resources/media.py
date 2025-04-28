from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models.files import File
from backend.models.media import Audio, Image, ImageFile, Person, Video, VideoFile
from backend.resources.base import ControlledSiteContentResource
from backend.resources.utils.import_export_widgets import (
    CustomManyToManyWidget,
    InvertedBooleanFieldWidget,
)


class BaseMediaResource(ControlledSiteContentResource):
    title = fields.Field(
        column_name="title",
        attribute="title",
    )

    description = fields.Field(column_name="description", attribute="description")

    acknowledgement = fields.Field(
        column_name="acknowledgement", attribute="acknowledgement"
    )

    exclude_from_kids = fields.Field(
        column_name="include_in_kids_site",
        attribute="exclude_from_kids",
        widget=InvertedBooleanFieldWidget(
            column="include_in_kids_site",
            default=False,
        ),
    )

    def before_import_row(self, row, **kwargs):
        # Filename to be used as title if not provided
        if "title" not in row:
            row["title"] = row["filename"]

        # Adding original
        associated_file = self.Meta.file_model.objects.filter(
            import_job__id=row["import_job"], content__contains=row["filename"]
        )[0]
        row["original"] = str(associated_file.id)

    class Meta:
        abstract = True
        clean_model_instances = True


class AudioResource(BaseMediaResource):
    original = fields.Field(
        column_name="original",
        attribute="original",
        widget=ForeignKeyWidget(model=File),
    )

    speakers = fields.Field(
        column_name="speaker",
        attribute="speakers",
        m2m_add=True,
        widget=CustomManyToManyWidget(
            model=Person, field="name", column_name="speaker"
        ),
    )

    exclude_from_games = fields.Field(
        column_name="include_in_games",
        attribute="exclude_from_games",
        widget=InvertedBooleanFieldWidget(column="include_in_games", default=False),
    )

    class Meta(BaseMediaResource.Meta):
        model = Audio
        file_model = File


class ImageResource(BaseMediaResource):
    original = fields.Field(
        column_name="original",
        attribute="original",
        widget=ForeignKeyWidget(model=ImageFile),
    )

    class Meta(BaseMediaResource.Meta):
        model = Image
        file_model = ImageFile


class VideoResource(BaseMediaResource):
    original = fields.Field(
        column_name="original",
        attribute="original",
        widget=ForeignKeyWidget(model=VideoFile),
    )

    class Meta:
        model = Video
        file_model = VideoFile
