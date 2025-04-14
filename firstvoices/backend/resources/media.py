from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models.files import File
from backend.models.media import Audio, Person
from backend.resources.base import (
    AudienceMixin,
    BaseImportWorkflowResource,
    ControlledSiteContentResource,
)
from backend.resources.utils.import_export_widgets import (
    CustomManyToManyWidget,
    InvertedBooleanFieldWidget,
)


class AudioResource(
    AudienceMixin, ControlledSiteContentResource, BaseImportWorkflowResource
):
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

    # To be used from audience mixin instead
    exclude_from_games = fields.Field(
        column_name="audio_include_in_games",
        attribute="exclude_from_games",
        widget=InvertedBooleanFieldWidget(
            column="audio_include_in_games", default=False
        ),
    )
    exclude_from_kids = fields.Field(
        column_name="audio_include_on_kids_site",
        attribute="exclude_from_kids",
        widget=InvertedBooleanFieldWidget(
            column="audio_include_on_kids_site", default=False
        ),
    )

    speakers = fields.Field(
        column_name="audio_speaker",
        attribute="speakers",
        m2m_add=True,
        widget=CustomManyToManyWidget(
            model=Person, field="name", column_name="audio_speaker"
        ),
    )

    def before_import_row(self, row, **kwargs):
        # title will be same as filename if not given
        if "audio_title" not in row:
            row["audio_title"] = row["audio_filename"]

        # Adding original
        associated_file = File.objects.filter(
            import_job__id=row["import_job"], content__contains=row["audio_filename"]
        )[0]
        row["audio_original"] = str(associated_file.id)

    class Meta:
        model = Audio
        clean_model_instances = True
