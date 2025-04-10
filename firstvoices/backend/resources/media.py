import uuid

from django.core.exceptions import ValidationError
from django.db import transaction
from import_export import fields
from import_export.results import RowResult
from import_export.widgets import ForeignKeyWidget

from backend.models.files import File
from backend.models.media import Audio
from backend.resources.base import AudienceMixin, ControlledSiteContentResource
from backend.resources.utils.import_export_widgets import InvertedBooleanFieldWidget


class AudioResource(AudienceMixin, ControlledSiteContentResource):
    # ["audio_filename",  "audio_speaker",]

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

    def __init__(self, site=None, run_as_user=None, import_job=None, **kwargs):
        super().__init__(**kwargs)
        self.site = site
        self.run_as_user = run_as_user
        self.import_job = import_job

    def before_import_row(self, row, **kwargs):
        # title will be same as filename if not given
        if "title" not in row:
            row["audio_title"] = row["audio_filename"]

        # todo: Figure out what to do if filenames are same
        # Adding original
        associated_file = File.objects.filter(
            import_job__id=row["import_job"], content__contains=row["audio_filename"]
        )[0]
        row["audio_original"] = str(associated_file.id)

    def import_row(self, row, instance_loader, **kwargs):
        # Marking erroneous and invalid rows as skipped, then clearing the errors and validation_errors
        # so the valid rows can be imported

        try:
            with transaction.atomic():
                import_result = super().import_row(row, instance_loader, **kwargs)
                import_result.error_messages = []  # custom field to store messages
                import_result.number = kwargs["row_number"]

                if import_result.import_type in [
                    RowResult.IMPORT_TYPE_ERROR,
                    RowResult.IMPORT_TYPE_INVALID,
                ]:
                    raise ValidationError("Row level error.")

        except ValidationError:
            if import_result.import_type == RowResult.IMPORT_TYPE_INVALID:
                import_result.error_messages = [
                    err for err in import_result.validation_error.messages
                ]
                import_result.validation_error = None
            else:
                import_result.error_messages = [
                    str(err.error).split("\n")[0] for err in import_result.errors
                ]
                import_result.errors = []

            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result

    def before_import(self, dataset, **kwargs):
        # Adding required columns, since these will not be present in the headers
        dataset.append_col(lambda x: str(uuid.uuid4()), header="id")
        dataset.append_col(lambda x: str(self.site.id), header="site")
        dataset.append_col(lambda x: str(self.run_as_user), header="created_by")
        dataset.append_col(lambda x: str(self.run_as_user), header="last_modified_by")
        dataset.append_col(lambda x: str(self.import_job), header="import_job")

    class Meta:
        model = Audio
        clean_model_instances = True
